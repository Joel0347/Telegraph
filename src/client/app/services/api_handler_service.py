import requests
from typing import Optional, Literal
from shared import publish_status, get_local_ip, get_local_port


class ApiHandlerService():
    _instance = None
    api_url: str = None
    
    def __new__(cls, api_url="http://identity-manager:8000"):
        if cls._instance is None:
            cls._instance = super(ApiHandlerService, cls).__new__(cls)
            cls._instance.api_url = api_url
        return cls._instance
    
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