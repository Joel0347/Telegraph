import requests, os, json, socket
from typing import Optional, Literal
from helpers import publish_status, get_local_ip, get_local_port, get_overlay_network


class ApiHandlerService():
    _instance = None
    api_urls: list[str] = None
    manager_leader_addr: str = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiHandlerService, cls).__new__(cls)
            cls._instance._discover_managers()
            cls._instance._find_leader_addr()
        return cls._instance
    
    def _discover_managers(self):
        udp_port = int(os.getenv("UDP_PORT", "5353"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        msg = {"action": "discover"}
        net = get_overlay_network()
        api_urls = set()

        try:
            # raise Exception()
            infos = socket.getaddrinfo("identity-manager", None)
            for info in infos:
                ip = info[4][0]
                api_urls.add(ip)
        except Exception:
            for ip in net.hosts():
                try:
                    sock.sendto(json.dumps(msg).encode(), (str(ip), udp_port))
                    data, _ = sock.recvfrom(1024)
                    response = json.loads(data.decode())

                    if response.get("status") == "active":
                        api_urls.add(str(ip))
                except Exception as e:
                    continue

        self.api_urls = list(api_urls)
    
    def _find_leader_addr(self):
        try:
            res = self._send_request_to_all("GET", "/managers/leader")
            if res.json()["status"] == 200:
                self.manager_leader_addr = res.json()["message"]
            else:
                publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
    
    def _send_request(self, method: str, path: str, **kwargs) -> requests.Response:
        res = requests.Response()
        res.status_code = 503
        res._content = b'{"message":"No hay lider disponible", "status": 500}'
        res.headers['Content-Type'] = 'application/json'
        api_port = int(os.getenv("API_PORT", "8000"))
        
        try:
            if not self.manager_leader_addr:
                self._find_leader_addr()
                
            res = requests.request(
                method, f"http://{self.manager_leader_addr}:{api_port}{path}",
                timeout=15, **kwargs
            )
        except Exception as e:
            ## comentar esta linea para no mostrar los managers caidos
            publish_status({'message': f"Error con {self.manager_leader_addr}: {e}", 'status': 500})
        
        return res
    
    def _send_request_to_all(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Helper que intenta la petición en todas las URLs de managers.
        Retorna la primera respuesta exitosa, o None si todas fallan.
        """

        res = requests.Response()
        res.status_code = 503
        res._content = b'{"message":"No managers disponibles", "status": 500}'
        res.headers['Content-Type'] = 'application/json'
        api_port = int(os.getenv("API_PORT", "8000"))

        for base_url in self.api_urls:
            try:
                tmp_res = requests.request(
                    method, f"http://{base_url}:{api_port}{path}",
                    timeout=10, **kwargs
                )

                if tmp_res.json()["status"] == 200:
                    res = tmp_res
                tmp_res.raise_for_status()
            except Exception as e:
                ## comentar esta linea para no mostrar los managers caidos
                publish_status({'message': f"Error con {base_url}: {e}", 'status': 500})
                continue
        return res

    def update_leader_addr(self, new_leader_addr: str):
        self.manager_leader_addr = new_leader_addr
        
    def get_peer_address(self, username: str) -> Optional[tuple]:
        try:
            res = self._send_request("GET", "/peers")
            peers: list[dict] = res.json().get("message", [])
            peer = next((p for p in peers if p["username"] == username), None)
            if peer:
                return peer.get("ip"), peer.get("port")
        except Exception:
            return None
        return None
    
    def get_users(self, username: str) -> list[dict]:
        try:
            res = self._send_request("GET", "/users")
            if res.json()["status"] == 200:
                return [
                    u["username"] for u in res.json()['message'] \
                        if u["username"] != username
                ]
            else:
                publish_status(res.json())
                return []
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return []

    def get_online_users(self, username: str) -> list[dict]:
        active_users = []
        try:
            all_users = self.get_users(username)
            for u in all_users:
                user_info = self.get_user_by_username(u)
                if user_info and user_info.get("status") == "online":
                    active_users.append(u)
                    
            return active_users
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            
    def get_user_by_username(self, username: str) -> dict:
        try:
            res = self._send_request("GET", f"/users/{username}")
            if res.json()["status"] == 200:
                return res.json()["message"]
            else:
                publish_status(res.json())
                return {}
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return {}
        
    def notify_online(self, username: str):
        try:
            res = self._send_request("GET", f"/users/{username}")
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
    
    def check_is_active(self, username: str) -> bool:
        try:
            res = self._send_request("GET", f"/users/active/{username}")
            publish_status(res.json())
            
            if res.json()["status"] == 200:
                return res.json()["message"] == "online"
            return False
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return False
        
    def send_heart_beat(self, username: str):
        res = self._send_request("POST", "/heartbeat", json={"username": username})
        publish_status(res.json())
            
    def logout(self, username: str):
        res = self._send_request("POST", "/logout", json={"username": username})
        publish_status(res.json())
            
    def login_register(self, username: str, pwd: str, action: Literal["login", "register"]) -> bool:
        try:
            res = self._send_request("POST", f"/{action}", json={
                "username": username,
                "password": pwd,
                "ip": get_local_ip(),
                "port": get_local_port(),
                "status": "online"
            })

            publish_status(res.json())
            return res.json()["status"] == 200
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})
            return False
        
    def update_ip_address(self, username: str):
        try:
            current_addr = get_local_ip()
            saved_addr = self.get_peer_address(username)

            if current_addr != saved_addr:
                res = self._send_request("PUT", f"/users/reconnect/{current_addr}/{username}")
                publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})