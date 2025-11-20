import requests, os, json, socket
from typing import Literal
from datetime import datetime
from helpers import publish_status, get_local_ip, get_overlay_network


class ManagerService():
    _instance = None
    _managers_ips: list[str] = None
    _managers_last_seen: dict[str, datetime] = None
    _leader_ip: str = None
    _status: Literal["leader", "candidate", "follower"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ManagerService, cls).__new__(cls)
            cls._instance._discover_managers()
            cls._instance._find_network_leader()
            cls._instance._notify_existence()
        return cls._instance
    
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

        self._managers_ips = list(managers)
        self._managers_last_seen = {mng: datetime.now() for mng in self._managers_ips}
    
    def _find_network_leader(self) -> dict:
        try:
            res = self._request_all("GET", f"/managers/leader")
            if res.json()["status"] == 200:
                self._leader_ip = res.json()["message"]
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {str(e)}", 'status': 500})
    
    def I_am_leader(self) -> bool:
        return self._status == "leader"
    
    def _request_all(self, method: str, path: str, **kwargs) -> requests.Response:
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
        
    def add_new_manager(self, ip: str):
        try:
            self._managers_ips.append(ip)
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
            res = self._request_all("POST", f"/managers/new/{ip}")
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {str(e)}", 'status': 500})
        
    def send_heart_beat(self):
        ip = get_local_ip()
        res = self._request_all("POST", f"/manager/heartbeat/{ip}")
        publish_status(res.json())

    def update_last_seen(self, ip: str) -> dict:
        if ip not in self._managers_last_seen:
            return {"message": f"{ip} not found", "status": 404}
        
        try:
            self._managers_last_seen[ip] = datetime.now()
            return {"message": "heartbeat rreceived", "status": 200}
        except Exception as e:
            return {"message": f"Error: {str(e)}", "status": 500}
