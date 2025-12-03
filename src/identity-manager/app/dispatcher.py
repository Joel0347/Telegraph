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
                "register": lambda data: cls._instance.register(data),
                "login": lambda data: cls._instance.login(data), 
                "logout": lambda data: cls._instance.logout(data) 
            }
            cls._instance.auth_service = auth_service
        return cls._instance
    
    
    def call(self, op: str, args: dict) -> Response:
        func = self._functionalities.get(op)
        if not func:
            raise ValueError(f"Operación desconocida: {op}")
        
        return func(args) if args else func()


    # --- Functionalities ---
    def register(self, data: dict):
        msg = self.auth_service.register_user(
            username=data.get("username", ""),
            password=data.get("password", ""),
            ip=data.get("ip", ""),
            port=data.get("port", 0),
        )
        return jsonify(msg)
    
    def login(self, data: dict):
        msg = self.auth_service.login_user(
            username=data.get("username", ""),
            password=data.get("password", ""),
            ip=data.get("ip", ""),
            port=data.get("port", 0),
        )
        return jsonify(msg)
    
    def logout(self, data: dict):
        username = data.get("username", "")
        msg = self.auth_service.update_status(
            username=username, status="offline"
        )
        return jsonify(msg)
        