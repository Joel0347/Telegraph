from typing import Literal
from repositories.user_repo import UserRepository
from models.user import User
from helpers import check_password, hash_password
from datetime import datetime


class ApiResponse(dict):
    def __init__(self, message: str, status: int):
        super().__init__(message=message, status=status)

class AuthService:
    _instance = None
    repo: UserRepository = None
    
    def __new__(cls, repo: UserRepository):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
            cls._instance.repo = repo
        return cls._instance


    def register_user(
            self, username: str, password: str,
            ip: str, port: int, status="online"
    ) -> ApiResponse:
        try:
            if not username or not password:
                return ApiResponse("Faltan datos", 400)
            
            existing = self.repo.find_by_username(username)
            if existing:
                return ApiResponse(
                    f"Usuario {username} ya se encuentra registrado", 409
                )

            user = User(
                username=username, ip=ip, port=port, status=status,
                password=hash_password(password),
                last_seen=datetime.now()
            )

            self.repo.add_user(user)
            return ApiResponse(f"Usuario {username} registrado correctamente", 200)

        except Exception as e:
            return ApiResponse(str(e), 500)
        

    def login_user(self, username, password, ip="", port=0)-> ApiResponse:
        try:
            user = self.repo.find_by_username(username)

            if not user:
                return ApiResponse("El usuario no existe", 500)
            
            if not check_password(password, user.password):
                return ApiResponse('Contraseña incorrecta', 409)
            
            if user.status == "online":
                return ApiResponse("Sesión ya iniciada", 403)
            
            user.ip = ip
            user.port = port
            user.status = "online"
            user.last_seen = datetime.now()
            self.repo.update_user(user)
            return ApiResponse('Login exitoso', 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
        
    def update_status(
            self, username: str, status: Literal["online", "offline"]
    ) -> ApiResponse:
        try:
            user = self.repo.find_by_username(username)
            if not user:
                return ApiResponse("El usuario no existe", 500)
            user.status = status
            self.repo.update_user(user)
            return ApiResponse('Estado actualizado exitosamente', 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
    
    def update_ip_address(self, username: str, ip: str) -> ApiResponse:
        try:
            user = self.repo.find_by_username(username)
            if not user:
                return ApiResponse("El usuario no existe", 500)
            user.ip = ip
            self.repo.update_user(user)
            return ApiResponse('IP actualizada exitosamente', 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
        
    def update(self, payload: dict) -> ApiResponse:
        try:
            username = payload.get("username", "")
            password = payload.get("password", "")
            ip = payload.get("ip", "")
            port = payload.get("port", 0)
            status = payload.get("status", "online")

            user = self.repo.find_by_username(username)
            if not user:
                return ApiResponse("El usuario no existe", 500)
            
            user.ip = ip
            user.password = password
            user.port = port
            user.status = status
            self.repo.update_user(user)
            return ApiResponse('Usuario actualizado exitosamente', 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
        
    def update_last_seen(self, username: str) -> ApiResponse:
        try:
            user = self.repo.find_by_username(username)
            if not user:
                return ApiResponse("El usuario no existe", 500)
            user.last_seen = datetime.now()
            self.repo.update_user(user)
            return ApiResponse('Última vez actualizada exitosamente', 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
    
    def get_peers(self) -> ApiResponse:
        users = self.repo.list_all()
        peers = [
            {"username": u.username, "ip": u.ip, "port": u.port}
            for u in users if u.ip and u.port
        ]
        return ApiResponse(peers, 200)

    def list_usernames(self) -> ApiResponse:
        users = self.repo.list_all()
        usernames = [{"username": u.username} for u in users]
        return ApiResponse(usernames, 200)
    
    def list_all(self) -> list[User]:
        return self.repo.list_all()
    
    def list_all_users_data(self) -> ApiResponse:
        users = self.repo.list_all()
        users_data = [u.model_dump(mode="json") for u in users]
        return ApiResponse(users_data, 200)
    
    def get_user_by_username(self, username: str) -> ApiResponse:
        try:
            user = self.repo.find_by_username(username)
            return ApiResponse(user.model_dump(mode="json"), 200)
        except Exception as e:
            return ApiResponse(str(e), 500)
        
    def reset(self):
        self.repo.reset()