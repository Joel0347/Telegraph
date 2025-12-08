import requests, os, json, socket, random, time, threading, logging
from threading import Lock
from enum import Enum
from typing import Dict, Any
from helpers import publish_status, get_local_ip, get_overlay_network
from services.log_service import LogService, LogRepository
from services.state_service import StateRepository, StateService
from dispatcher import Dispatcher


class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class ManagerService():
    _instance = None
    _log_service: LogService = None
    _state_service: StateService = None
    _managers_ips: set[str] = None
    _leader_ip: str = None
    _current_term: int = None
    _heartbeat_stop: threading.Event = None
    _heartbeat_thread = None
    _status: NodeState = None
    _k: int = None
    _node_id: str = None
    _port: int = None
    _election_timeout: float = None
    _election_timer: threading.Timer = None
    _last_heartbeat: float = None
    _next_index: dict = None
    _match_index: dict = None
    _log: list = None
    _voted_for: str = None
    _commit_index: int = None
    _last_applied: int = None
    _dispatcher: Dispatcher = None
    _lock: Lock = None
    
    def __new__(cls, dispatcher: Dispatcher):
        if cls._instance is None:
            cls._instance = super(ManagerService, cls).__new__(cls)
            cls._instance._k = int(os.getenv("K", "2")) # parametrizable
            cls._instance._lock = Lock()
            cls._instance._dispatcher = dispatcher
            cls._instance._node_id = get_local_ip()
            cls._instance._port = 8000
            cls._instance._discover_managers()
            cls._instance._status = NodeState.FOLLOWER
            cls._instance._log_service = LogService(LogRepository())
            cls._instance._state_service = StateService(StateRepository())
            cls._instance._find_network_leader()
            cls._instance._notify_existence()
            # ========== Codigo de Raft =========
            cls._instance._setup_logging()
            cls._instance._load_persistent_state()
            
            # Leader state
            cls._instance._next_index = {}
            cls._instance._match_index = {}
            
            # Election timeout (alineado con heartbeats)
            cls._instance._election_timeout = random.uniform(3.0, 5.0)
            cls._instance._last_heartbeat = time.time()

            # Heartbeat loop
            cls._instance._heartbeat_stop = threading.Event()
            # ===================================
            
            cls._instance.start()
        return cls._instance
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - {self._node_id} - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging configured for node {self._node_id}")
    
    def _load_persistent_state(self):
        current_state = self._state_service.load()
        if current_state["status"] == 200:
            state_data: dict = current_state["message"]
            self._current_term = state_data.get("current_term", 0)
            self._voted_for = state_data.get("voted_for", None)
            self._commit_index = state_data.get("commit_index", -1)
            self._last_applied = state_data.get("last_applied", -1)
            self.logger.info(f"Loaded state: term={self._current_term}, voted_for={self._voted_for}, "
                f"commit_index={self._commit_index}, last_applied={self._last_applied}")

        self._log = [log.model_dump(mode="json") for log in self._log_service.list_all()]
        self.logger.info(f"Loaded log with {len(self._log)} entries")

    def _save_persistent_state(self):
        payload = {
            "current_term": self._current_term,
            "voted_for": self._voted_for,
            "commit_index": self._commit_index,
            "last_applied": self._last_applied
        }
        
        self._state_service.update(payload)
        self.logger.debug("Persistent state saved successfully")

    def _save_log_entry(self, entry: Dict[str, Any]):
        res = self._log_service.add_log(entry)
        
        if res["status"] == 200:
            self.logger.debug(f"Log entry saved: index={entry.get('index')}")
            self._log.append(entry)
        else:
            self.logger.error(f"Error saving log entry: {res['message']}")
        
    def update_term_and_vote(self, term: int, voted_for: str = None):
        """Actualiza el término y voto de manera persistente"""
        self._current_term = term
        self._voted_for = voted_for
        self._save_persistent_state()
        self.logger.info(f"Updated term to {term}, voted_for: {voted_for}")
    
    def start(self):
        """Inicia el nodo Raft"""
        self.logger.info(f"Starting Raft node {self._node_id} on port {self._port}")
        self.reset_election_timer()
    
    def reset_election_timer(self):
        """Reinicia el temporizador de elección"""
        if self._election_timer:
            self._election_timer.cancel()
        
        self._election_timeout = random.uniform(3.0, 5.0)
        self._election_timer = threading.Timer(self._election_timeout, self.start_election)
        self._election_timer.start()
        self.logger.debug("Election timer reset")
        
    def start_election(self):
        """Inicia una elección para líder"""
        if self.I_am_leader():
            return
            
        self.logger.info("Election timeout - starting new election")
        self._status = NodeState.CANDIDATE
        self._current_term += 1
        self._voted_for = self._node_id
        self._save_persistent_state()
        
        # Votar por sí mismo
        votes_received = 1
        
        # Solicitar votos de otros nodos
        for peer in self._managers_ips:
            if self.request_vote(peer):
                votes_received += 1
        
        # Verificar si ganó la elección
        if votes_received > self._k:
            self.become_leader()
        else:
            self._status = NodeState.FOLLOWER
            self.reset_election_timer()
    
    def request_vote(self, peer_ip: str) -> bool:
        """Solicita voto a un nodo peer"""
        try:
            peer_port = 8000
            response = requests.post(
                f"http://{peer_ip}:{peer_port}/request_vote",
                json={
                    "term": self._current_term,
                    "candidate_id": self._node_id,
                    "last_log_index": len(self._log) - 1,
                    "last_log_term": self._log[-1]["term"] if self._log else 0
                },
                timeout=3.0
            )
            return response.json().get("vote_granted", False)
        except Exception as e:
            self.logger.debug(f"Failed to request vote from {peer_ip}: {e}")
            return False
    
    def become_leader(self):
        """Convierte el nodo en líder"""
        self.logger.info(f"Becoming leader for term {self._current_term}")
        self._status = NodeState.LEADER
        self._leader_ip = get_local_ip()
        self._send_request_to_all_managers("POST", f"/new_leader/{self._leader_ip}")
        self._send_request_to_all_clients("POST", f"/new_leader/{self._leader_ip}")
        # logica para expandir la noticia de mi liderazgo a los clientes
        
        # Inicializar estado del líder
        for peer in self._managers_ips:
            self._next_index[peer] = len(self._log)
            self._match_index[peer] = 0
        
        # Iniciar loop de heartbeats
        self.start_heartbeat_loop(interval=1.0)
    
    def start_heartbeat_loop(self, interval: float = 1.0):
        """Loop dedicado para enviar heartbeats sin encadenar timers"""
        # Detener loop previo si existe
        self._heartbeat_stop.set()
        self._heartbeat_stop = threading.Event()

        def loop():
            while not self._heartbeat_stop.is_set():
                if self.I_am_leader():
                    for peer in self._managers_ips:
                        threading.Thread(
                            target=self.send_append_entries,
                            args=(peer,), daemon=True
                        ).start()
                time.sleep(interval)

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        
        self._heartbeat_thread = threading.Thread(target=loop, daemon=True)
        self._heartbeat_thread.start()
        
    def send_append_entries(self, peer_ip: str):
        """Envía AppendEntries RPC a un follower"""
        try:
            peer_port = 8000
            next_index = self._next_index.get(peer_ip, 0)
            prev_log_index = next_index - 1
            prev_log_term = self._log[prev_log_index]["term"] if prev_log_index >= 0 else 0
            
            entries = self._log[next_index:] if next_index < len(self._log) else []
            
            response = requests.post(
                f"http://{peer_ip}:{peer_port}/append_entries",
                json={
                    "term": self._current_term,
                    "leader_id": self._node_id,
                    "prev_log_index": prev_log_index,
                    "prev_log_term": prev_log_term,
                    "entries": entries,
                    "leader_commit": self._commit_index
                },
                timeout=3.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self._next_index[peer_ip] = next_index + len(entries)
                    self._match_index[peer_ip] = self._next_index[peer_ip] - 1
                    self.logger.debug(
                        f"AppendEntries successful for {peer_ip},"
                        f"next_index: {self._next_index[peer_ip]}"
                    )
                else:
                    self._next_index[peer_ip] = max(0, next_index - 1)
                    self.logger.debug(
                        f"AppendEntries failed for {peer_ip}, decrementing next_index to " +
                        f"{self._next_index[peer_ip]}"
                    )
        except Exception as e:
            self.logger.error(f"Error sending append entries to {peer_ip}: {e}")


    def handle_request_vote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja solicitudes de voto"""
        term = data["term"]
        candidate_id = data["candidate_id"]
        last_log_index = data["last_log_index"]
        last_log_term = data["last_log_term"]
        
        # Verificar term
        if term < self._current_term:
            self.logger.debug(
                f"Rejecting vote request from {candidate_id}: term {term}" +
                f" < current term {self._current_term}"
            )
            return {"term": self._current_term, "vote_granted": False}
        
        # Actualizar term si es necesario
        if term > self._current_term:
            self.update_term_and_vote(term)
            self._status = NodeState.FOLLOWER
            self._voted_for = None
        
        # Verificar condiciones para votar
        can_vote = (
            self._voted_for is None or self._voted_for == candidate_id
        ) and self.is_candidate_log_up_to_date(last_log_index, last_log_term)
        
        if can_vote:
            self._voted_for = candidate_id
            self._save_persistent_state()
            self.reset_election_timer()
            self.logger.info(f"Voted for {candidate_id} in term {term}")
            return {"term": self._current_term, "vote_granted": True}
        else:
            self.logger.debug(f"Rejecting vote request from {candidate_id}: voting conditions not met")
            return {"term": self._current_term, "vote_granted": False}

    def is_candidate_log_up_to_date(self, last_log_index: int, last_log_term: int) -> bool:
        """Verifica si el log del candidato está actualizado"""
        if not self._log:
            return True
            
        our_last_log_term = self._log[-1]["term"]
        our_last_log_index = len(self._log) - 1
        
        if last_log_term > our_last_log_term:
            return True
        elif last_log_term == our_last_log_term and last_log_index >= our_last_log_index:
            return True
        else:
            return False
    
    def handle_append_entries(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja AppendEntries RPC con persistencia"""
        term = data["term"]
        leader_id = data["leader_id"]
        prev_log_index = data["prev_log_index"]
        prev_log_term = data["prev_log_term"]
        entries = data["entries"]
        leader_commit = data["leader_commit"]
        
        # Verificar term
        if term < self._current_term:
            self.logger.debug(
                f"Rejecting AppendEntries from {leader_id}: term {term}" +
                f" < current term {self._current_term}"
            )
            return {"term": self._current_term, "success": False}
        
        # Reiniciar election timer
        self.reset_election_timer()
        
        # Convertirse en follower si es necesario
        if term > self._current_term:
            self.update_term_and_vote(term)
            self._status = NodeState.FOLLOWER
            self._voted_for = None
        
        # Verificar consistencia del log
        if prev_log_index >= 0:
            if prev_log_index >= len(self._log) or self._log[prev_log_index]["term"] != prev_log_term:
                self.logger.debug(f"Log inconsistency at index {prev_log_index}")
                return {"term": self._current_term, "success": False}
        
        # Añadir entradas al log con persistencia
        if entries:
            if prev_log_index + 1 < len(self._log):
                # Eliminar entradas en conflicto y guardar
                self._log_service.delete_log_entries(prev_log_index + 1, len(self._log))
                self._log = self._log[:prev_log_index + 1]
                self.logger.info(f"Trimmed log to index {prev_log_index}")
            
            # Añadir nuevas entradas con persistencia
            for entry in entries:
                self._save_log_entry(entry)
            self.logger.info(f"Added {len(entries)} new log entries from leader {leader_id}")
        
        # Actualizar commit index desde el líder y aplicar
        if leader_commit > self._commit_index:
            old_commit = self._commit_index
            self._commit_index = min(leader_commit, len(self._log) - 1)
            if old_commit != self._commit_index:
                self.logger.info(f"Updated commit index from {old_commit} to {self._commit_index}")
            self.apply_committed_entries()
            self._save_persistent_state()  # Persistir nuevo commit y last_applied
        
        return {"term": self._current_term, "success": True}
    
    def handle_client_request(self, op: str, args: dict) -> dict:
        """Maneja solicitudes de clientes para añadir datos al log"""
        if not self.I_am_leader():
            # Redirigir al líder si este nodo no es el líder
            leader = self._find_network_leader()
            if leader:
                self.logger.info(f"Redirecting client to leader: {leader}")
                return {"success": False, "leader": leader}
            else:
                self.logger.warning("No leader available for client request")
                return {"succes": False, "message": "no_leader_available"}
        
        try:
            with self._lock:
                # Crear nueva entrada de log
                new_entry = {
                    "term": self._current_term,
                    "index": len(self._log),
                    "op": op,
                    "args": args,
                    "applied": False
                }
                
                # Añadir al log local
                self._save_log_entry(new_entry)
                self.logger.info(f"Added client data to log at index {new_entry['index']}")
                
                # Replicar a los followers
                success_count = 1  # Contamos al líder mismo
                
                for peer in self._managers_ips:
                    if self.replicate_to_follower(peer, new_entry):
                        success_count += 1
                
                # Verificar si se alcanzó la mayoría
                if success_count > self._k:
                    # Commit la entrada en el líder
                    self._commit_index = new_entry["index"]
                    self.apply_committed_entries()
                    self._save_persistent_state()  # comprometer commit/last_applied en disco

                    # Propagar inmediatamente el nuevo commit a los followers (AppendEntries vacío)
                    for peer in self._managers_ips:
                        threading.Thread(target=self.send_append_entries, args=(peer,), daemon=True).start()

                    self.logger.info(f"Successfully committed client data at index {new_entry['index']}")
                    return {"success": True, "message": ""}
                else:
                    self._log_service.delete_log_by_index(new_entry['index'])
                    self._log.pop()
                    self.logger.error(
                        "Failed to replicate client data to majority, " + 
                        f"reverted entry at index {new_entry['index']}"
                    )
                    return {"success": False, "message": "Failed when replicating"}
            
        except Exception as e:
            return {"success": False, "message": f"{e}"}
        
        
    def replicate_to_follower(self, peer_ip: str, entry: Dict[str, Any]) -> bool:
        """Replica una entrada a un follower específico"""
        try:
            peer_port = 8000
            response = requests.post(
                f"http://{peer_ip}:{peer_port}/append_entries",
                json={
                    "term": self._current_term,
                    "leader_id": self._node_id,
                    "prev_log_index": entry["index"] - 1,
                    "prev_log_term": self._log[entry["index"] - 1]["term"] if entry["index"] > 0 else 0,
                    "entries": [entry],
                    "leader_commit": self._commit_index
                },
                timeout=3.0
            )
            success = response.json().get("success", False)
            if success:
                self.logger.debug(f"Successfully replicated to {peer_ip}")
            else:
                self.logger.debug(f"Failed to replicate to {peer_ip}")
            return success
        except Exception as e:
            self.logger.debug(f"Error replicating to {peer_ip}: {e}")
            return False
        
    def apply_committed_entries(self):
        """Aplica las entradas comprometidas al estado de la máquina"""
        while self._last_applied < self._commit_index:
            self._last_applied += 1
            # Seguridad: evitar índice fuera de rango si commit apunta a más que el log
            if 0 <= self._last_applied < len(self._log):
                entry = self._log[self._last_applied]
                self.apply_entry_to_state_machine(entry)
            else:
                self.logger.error(f"Commit index {self._commit_index} beyond log length {len(self._log)}")
                break
    
    def apply_entry_to_state_machine(self, entry: Dict[str, Any]):
        """Aplica una entrada al estado de la máquina (evita duplicados)"""
        self.logger.info(f"Applying entry {entry['index']} to state machine")
        
        try:
            applied_data = []
            applied_data = self._log_service.find_by_applied_criteria(True)
            # Evitar duplicados por (index, term)
            already = any(
                (e.index == entry.get("index") and e.term == entry.get("term"))
                for e in applied_data
            )
            if already:
                self.logger.debug(f"Entry index={entry['index']} term={entry['term']} already applied; skipping.")
                return
            
            self._log_service.update_applied(entry["index"], True)
            
            if not self.I_am_leader():
                self._dispatcher.call(entry["op"], entry["args"])
                
            self.logger.debug(f"Applied data saved")
                
        except Exception as e:
            self.logger.error(f"Error applying entry to state machine: {e}")

    # region ======== Codigo del Servicio original =========
    
    def _discover_managers(self):
        udp_port = int(os.getenv("UDP_PORT", "5353"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        msg = {"action": "discover"}
        net = get_overlay_network()
        managers = set()

        try:
            # raise Exception()
            infos = socket.getaddrinfo("identity-manager", None)
            for info in infos:
                ip = info[4][0]
                managers.add(ip)
        except Exception:
            for ip in net.hosts():
                try:
                    sock.sendto(json.dumps(msg).encode(), (str(ip), udp_port))
                    data, _ = sock.recvfrom(1024)
                    response = json.loads(data.decode())

                    if response.get("status") == "active":
                        managers.add(str(ip))
                except Exception:
                    continue

        self._managers_ips = managers
        self._managers_ips.remove(get_local_ip())
    
    def _find_network_leader(self) -> str:
        if self._leader_ip:
            return self._leader_ip
        
        try:
            res = self._send_request_to_all_managers("GET", f"/managers/leader")
            if res.json()["status"] == 200:
                self._leader_ip = res.json()["message"]
                return self._leader_ip
            else:
                self._leader_ip = None
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {str(e)}", 'status': 500})
        
        return None
    
    def I_am_leader(self) -> bool:
        return self._status == NodeState.LEADER
    
    def _send_request_to_all_managers(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Helper que intenta la petición en todas las URLs de managers.
        Retorna la primera respuesta exitosa, o None si todas fallan.
        """

        res = requests.Response()
        res.status_code = 503
        res._content = b'{"message":"No managers disponibles", "status": 500}'
        res.headers['Content-Type'] = 'application/json'
        api_port = 8000

        for manager in self._managers_ips:
            try:
                tmp_res = requests.request(
                    method, f"http://{manager}:{api_port}{path}",
                    timeout=2, **kwargs
                )

                if tmp_res.json()["status"] == 200:
                    res = tmp_res
                tmp_res.raise_for_status()
            except Exception as e:
                ## comentar esta linea para no mostrar los managers caidos
                publish_status({'message': f"Error con {manager}: {str(e)}", 'status': 500})
                continue
        return res
    
    def _send_request_to_all_clients(self, method: str, path: str, **kwargs):
        users = self._dispatcher.auth_service.list_all()
        for user in users:
            try:
                res = requests.request(
                    method, f"http://{user.ip}:{user.port}{path}",
                    timeout=2, **kwargs
                )
                res.raise_for_status()
            except Exception as e:
                publish_status({'message': f"Error con {user}: {str(e)}", 'status': 500})
                continue
        
    def add_new_manager(self, ip: str):
        try:
            self._managers_ips.add(ip)
            return {"message": "OK", "status": 200}
        except Exception as e:
            return {"message": f"ERROR: {str(e)}", "status": 500}
    
    def get_leader(self) -> str:
        if leader := self._leader_ip:
            return {"message": leader, "status": 200}
        else:
            return {"message": f"No leader known yet", "status": 404}

    def _notify_existence(self) -> dict:
        try:
            ip = get_local_ip()
            res = self._send_request_to_all_managers("POST", f"/managers/new/{ip}")
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {str(e)}", 'status': 500})
        
    def update_leader(self, new_leader_addr: str):
        try:
            self._leader_ip = new_leader_addr
            return {"message": "Leader updated succesfully", "status": 200}
        except Exception as e:
            return {"message": f"Error updating leader: {e}", "status": 500}
