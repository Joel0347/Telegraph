import requests
from typing import Optional
from shared import publish_status


class ApiHandlerService():
    _instance = None
    identity_manager_url: str = None
    
    def __new__(cls, identity_manager_url="http://identity-manager:8000"):
        if cls._instance is None:
            cls._instance = super(ApiHandlerService, cls).__new__(cls)
            cls._instance.identity_manager_url = identity_manager_url
        return cls._instance
    
    def get_peer_address(self, username: str) -> Optional[tuple]:
        try:
            res = requests.get(f"{self.identity_manager_url}/peers", timeout=2)
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
            res = requests.get(f"{self.identity_manager_url}/users")
            if res.json()["status"] == 200:
                return [u["username"] for u in res.json()['usernames'] if u["username"] != username]
            else:
                publish_status(res.json())
                return []
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
        
    def send_heart_beat(self, username: str):
        try:
            res = requests.post(f"{self.identity_manager_url}/heartbeat", json={"username": username})
            if res["status"] != 200:
                publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado {e}", 'status': 500})
            
    def logout(self, username: str):
        try:
            res = requests.post(f"{self.identity_manager_url}/logout", json={"username": username})
            publish_status(res.json())
        except Exception as e:
            publish_status({'message': f"Error inesperado: {e}", 'status': 500})