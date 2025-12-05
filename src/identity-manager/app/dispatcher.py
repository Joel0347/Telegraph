from services.auth_service import AuthService
from flask import jsonify, Response


class Dispatcher:
    _instance = None
    _functionalities: dict = None
    auth_service: AuthService = None
    
    def __new__(cls, auth_service: AuthService):
        if cls._instance is None:
            cls._instance = super(Dispatcher, cls).__new__(cls)
            cls._instance._functionalities = {
                "register": cls._instance.register,
                "login": cls._instance.login, 
                "logout": cls._instance.logout,
                "get_peers": cls._instance.get_peers,
                "list_users": cls._instance.list_users,
                "find_by_username": cls._instance.find_by_username,
                "notify_online": cls._instance.notify_online,
                "heartbeat": cls._instance.heartbeat,
                "is_user_active": cls._instance.is_user_active,
                "update_ip_address": cls._instance.update_ip_address
            }
            cls._instance.auth_service = auth_service
        return cls._instance
    
    
    def call(self, op: str, args: dict) -> Response:
        func = self._functionalities.get(op)
        if not func:
            raise ValueError(f"Operación desconocida: {op}")
        
        return func(args) if args else func()


    # --- Functionalities ---
    def register(self, data: dict) -> Response:
        msg = self.auth_service.register_user(
            username=data.get("username", ""),
            password=data.get("password", ""),
            ip=data.get("ip", ""),
            port=data.get("port", 0),
        )
        return jsonify(msg)
    
    def login(self, data: dict) -> Response:
        msg = self.auth_service.login_user(
            username=data.get("username", ""),
            password=data.get("password", ""),
            ip=data.get("ip", ""),
            port=data.get("port", 0),
        )
        return jsonify(msg)
    
    def logout(self, data: dict) -> Response:
        username = data.get("username", "")
        msg = self.auth_service.update_status(
            username=username, status="offline"
        )
        return jsonify(msg)
        
    def get_peers(self) -> Response:
        peers = self.auth_service.get_peers()
        return jsonify({"peers": peers, "status": 200})

    def list_users(self) -> Response:
        usernames = self.auth_service.list_usernames()
        return jsonify({"usernames": usernames, "status": 200})

    def find_by_username(self, data: dict) -> Response:
        username = data.get("username", "")
        msg = self.auth_service.get_user_by_username(username)
        return jsonify(msg)
    
    def notify_online(self, data: dict) -> Response:
        username = data.get("username", "")
        msg = self.auth_service.update_status(username, "online")
        return jsonify(msg)

    def heartbeat(self, data: dict) -> Response:
        username = data.get("username")
        
        if not username:
            return jsonify({"message": "username requerido", "status": 400})

        try:
            self.auth_service.update_last_seen(username)
            return jsonify({"message": "heartbeat recibido", "status": 200})
        except Exception as e:
            return jsonify({"message": str(e), "status": 500})

    def is_user_active(self, data: dict) -> Response:
        username = data.get("username")
        msg = self.auth_service.get_user_by_username(username)
    
        if msg["status"] == 500:
            return jsonify(msg)
        
        return jsonify({"message": msg["message"]["status"], "status": 200})

    def update_ip_address(self, data: dict) -> Response:
        username = data.get("username")
        ip = data.get("ip")
        msg = self.auth_service.update_ip_address(username, ip)
        return jsonify(msg)
