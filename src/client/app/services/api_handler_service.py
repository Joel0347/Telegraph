import requests, os , json, socket
from typing import Optional, Literal
from helpers import publish_status, get_local_ip, get_local_port, get_network_broadcast


class ApiHandlerService():
    _instance = None
    api_url: str = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiHandlerService, cls).__new__(cls)
            cls._instance.discover_manager()
        return cls._instance
    
    def discover_manager(self):
        dns_port = int(os.getenv("DNS_PORT", "5353"))
        broadcast_ip = get_network_broadcast()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        msg = {"action": "discover"}
        sock.sendto(json.dumps(msg).encode(), (broadcast_ip, dns_port))

        data, _ = sock.recvfrom(1024)
        response = json.loads(data.decode())
        self.api_url = f"http://{response['ip']}:{int(response['port'])}"
    
    def get_peer_address(self, username: str) -> Optional[tuple]:
        try:
            res = requests.get(f"{self.api_url}/peers", timeout=2)
            res.raise_for_status()
            peers = res.json().get("peers", [])
            peer = next((p for p in peers if p["username"] == username), None)
            if peer:
                return peer.get("ip"), peer.get("port")
        except Exception:
            return None
        return None
    
    def get_users(self, username: str) -> list[dict]:
        try:
            res = requests.get(f"{self.api_url}/users")
            if res.json()["status"] == 200:
                return [u["username"] for u in res.json()['usernames'] if u["username"] != username]
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
            res = requests.get(f"{self.api_url}/users/{username}")
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
            res = requests.get(f"{self.api_url}/users/{username}")
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
    
    def check_is_active(self, username: str) -> bool:
        try:
            res = requests.get(f"{self.api_url}/users/active/{username}")
            publish_status(res.json())
            
            if res.json()["status"] == 200:
                return res.json()["message"] == "online"
            return False
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            return False
        
    def send_heart_beat(self, username: str):
        try:
            res = requests.post(f"{self.api_url}/heartbeat", json={"username": username})
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            
    def logout(self, username: str):
        try:
            res = requests.post(f"{self.api_url}/logout", json={"username": username})
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})
            
    def login_register(self, username: str, pwd: str, action: Literal["login", "register"]) -> bool:
        try:
            res = requests.post(f"{self.api_url}/{action}", json={
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
                res = requests.put(f"{self.api_url}/users/reconnect/{current_addr}/{username}")
                publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})