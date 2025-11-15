import requests, os, json, socket
from typing import Optional, Literal
from helpers import publish_status, get_local_ip, get_local_port, get_overlay_network


class ApiHandlerService():
    _instance = None
    api_urls: list[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiHandlerService, cls).__new__(cls)
            cls._instance._discover_managers()
        return cls._instance
    
    def _discover_managers(self):
        dns_port = int(os.getenv("DNS_PORT", "5353"))
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
                    sock.sendto(json.dumps(msg).encode(), (str(ip), dns_port))
                    data, _ = sock.recvfrom(1024)
                    response = json.loads(data.decode())

                    if response.get("status") == "active":
                        api_urls.add(str(ip))
                except Exception as e:
                    continue

        self.api_urls = list(api_urls)
    
    def _request_all(self, method: str, path: str, **kwargs):
        """
        Helper que intenta la petición en todas las URLs de managers.
        Retorna la primera respuesta exitosa, o None si todas fallan.
        """
        res = None
        api_port = int(os.getenv("API_PORT", "8000"))
        for base_url in self.api_urls:
            try:
                res = requests.request(
                    method, f"http://{base_url}:{api_port}{path}",
                    timeout=2, **kwargs
                )
                res.raise_for_status()
            except Exception as e:
                publish_status({'message': f"Error con {base_url}: {e}", 'status': 500})
                continue
        return res

    
    def get_peer_address(self, username: str) -> Optional[tuple]:
        try:
            # res = requests.get(f"{self.api_urls}/peers", timeout=2)
            res = self._request_all("GET", "/peers")
            # res.raise_for_status()
            peers = res.json().get("peers", [])
            peer = next((p for p in peers if p["username"] == username), None)
            if peer:
                return peer.get("ip"), peer.get("port")
        except Exception:
            return None
        return None
    
    def get_users(self, username: str) -> list[dict]:
        try:
            # res = requests.get(f"{self.api_urls}/users")
            res = self._request_all("GET", "/users")
            if res.json()["status"] == 200:
                return [u["username"] for u in res.json()['usernames'] if u["username"] != username]
            else:
                # publish_status(res.json())
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
            res = self._request_all("GET", f"/users/{username}")
            # res = requests.get(f"{self.api_urls}/users/{username}")
            if res.json()["status"] == 200:
                return res.json()["message"]
            else:
                # publish_status(res.json())
                return {}
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return {}
        
    def notify_online(self, username: str):
        try:
            # res = requests.get(f"{self.api_urls}/users/{username}")
            self._request_all("GET", f"/users/{username}")
            # publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
    
    def check_is_active(self, username: str) -> bool:
        try:
            # res = requests.get(f"{self.api_urls}/users/active/{username}")
            res = self._request_all("GET", f"/users/active/{username}")
            # publish_status(res.json())
            
            if res.json()["status"] == 200:
                return res.json()["message"] == "online"
            return False
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return False
        
    def send_heart_beat(self, username: str):
        # try:
        self._request_all("POST", "/heartbeat", json={"username": username})
            # publish_status(res.json())
        # except Exception as e:
        #     publish_status({'message': f"Error inesperado {e}", 'status': 500})
            
    def logout(self, username: str):
        self._request_all("POST", "/logout", json={"username": username})
        # try:
        #     res = requests.post(f"{self.api_urls}/logout", json={"username": username})
        #     publish_status(res.json())
        # except Exception as e:
        #     publish_status({'message': f"Error inesperado: {e}", 'status': 500})
            
    def login_register(self, username: str, pwd: str, action: Literal["login", "register"]) -> bool:
        try:
            res = self._request_all("POST", f"/{action}", json={
                "username": username,
                "password": pwd,
                "ip": get_local_ip(),
                "port": get_local_port(),
                "status": "online"
            })
            # res = requests.post(f"{self.api_urls}/{action}", json={
            #     "username": username,
            #     "password": pwd,
            #     "ip": get_local_ip(),
            #     "port": get_local_port(),
            #     "status": "online"
            # })
            # publish_status(res.json())
            
            return res.json()["status"] == 200
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})
            return False
        
    def update_ip_address(self, username: str):
        try:
            current_addr = get_local_ip()
            saved_addr = self.get_peer_address(username)

            if current_addr != saved_addr:
                self._request_all("PUT", f"/users/reconnect/{current_addr}/{username}")
                # res = requests.put(f"{self.api_urls}/users/reconnect/{current_addr}/{username}")
                # publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})