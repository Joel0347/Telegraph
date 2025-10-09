from bcrypt import hashpw, checkpw, gensalt
from typing import Tuple, Literal
from repositories.user_repo import UserRepository
from models.user import User
from datetime import datetime


class AuthService:
    _instance = None
    repo: UserRepository = None
    
    def __new__(cls, repo: UserRepository):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
            cls._instance.repo = repo
        return cls._instance


    @staticmethod
    def hash_password(plaintext_password: str) -> str:
        """
        Hashes a plaintext password using bcrypt and returns the hashed password as a UTF-8 string.

        Args:
            planetext_password (str): The plaintext password to hash.

        Returns:
            str: The bcrypt-hashed password.
        """
        return hashpw(plaintext_password.encode('utf-8'), gensalt()).decode('utf-8')

    @staticmethod
    def check_password(plain_pwd: str, hashed_pwd: str) -> bool:
        """
        Checks whether a password is correct or not.

        Args:
            plain_pwd (str): The plain password inserted by user.
            hashed_pwd (str): The hashed password saved in database.

        Returns:
            bool: `True` if `plain_pwd` is the correct password, otherwise `False`
        """
        return checkpw(plain_pwd.encode('utf-8'), hashed_pwd.encode('utf-8'))

    def register_user(self, username: str, password: str, ip: str = "", port: int = 0) -> Tuple[bool, str]:
        try:
            if not username or not password:
                return {"message": "Faltan datos", "status": 400}
            
            existing = self.repo.find_by_username(username)
            if existing:
                return {
                    "message": f"Usuario {username} ya se encuentra registrado",
                    "status": 409
                }

            user = User(
                username=username, ip=ip, port=port, status="online",
                password=AuthService.hash_password(password),
                last_seen=datetime.now()
            )

            self.repo.add_user(user)
            return {
                "message": f"Usuario {username} registrado correctamente",
                "status": 200
            }

        except Exception as e:
            return {"message": str(e), "status": 500}
        

    def login_user(self, username, password, ip="", port=0)-> Tuple[bool, str]:
        try:
            user = self.repo.find_by_username(username)

            if not user:
                return {"message": "El usuario no existe", "status": 500}
            
            if not AuthService.check_password(password, user.password):
                return {"message": 'Contraseña incorrecta', "status": 409}
            
            if user.status == "online":
                return {
                    "message": "Sesión ya iniciada",
                    "status": 403
                }
            
            user.ip = ip
            user.port = port
            user.status = "online"
            user.last_seen = datetime.now()
            self.repo.update_user(user)
            return {"message": 'Login exitoso', "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}
        
    def update_status(self, username: str, status: Literal["online", "offline"]):
        try:
            user = self.repo.find_by_username(username)
            if not user:
                return {"message": "El usuario no existe", "status": 500}
            user.status = status
            self.repo.update_user(user)
            return {"message": 'Estado actualizado exitosamente', "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}
        
    def update_last_seen(self, username: str):
        try:
            user = self.repo.find_by_username(username)
            if not user:
                return {"message": "El usuario no existe", "status": 500}
            user.last_seen = datetime.now()
            self.repo.update_user(user)
            return {"message": 'Última vez actualizada exitosamente', "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}

    
    def get_peers(self) -> list[dict]:
        users = self.repo.list_all()
        return [
            {"username": u.username, "ip": u.ip, "port": u.port}
            for u in users if u.ip and u.port
        ]

    def list_usernames(self) -> list[dict]:
        users = self.repo.list_all()
        return [{"username": u.username} for u in users]
    
    def list_all(self) -> list[User]:
        return self.repo.list_all()
    
    def get_user_by_username(self, username: str) -> dict:
        try:
            user = self.repo.find_by_username(username)
            return {"message": user.model_dump(mode="json"), "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}