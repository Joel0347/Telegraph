import os
from threading import Lock

class ClientRepository:
    _instance = None
    _lock: Lock = None
    base_folder: str = None
    env_path: str = None

    def __new__(cls, base_folder: str = "/data"):
        if cls._instance is None:
            cls._instance = super(ClientRepository, cls).__new__(cls)
            cls._instance.base_folder = base_folder
            cls._instance.env_path = os.path.join(base_folder, ".env")
            cls._instance._lock = Lock()
            os.makedirs(cls._instance.base_folder, exist_ok=True)
        return cls._instance

    def save_username(self, username: str) -> None:
        with self._lock:
            with open(self.env_path, "w") as f:
                f.write(f"USERNAME={username}\n")

    def load_username(self) -> str | None:
        with self._lock:
            if not os.path.exists(self.env_path):
                return None
            with open(self.env_path) as f:
                for line in f:
                    if line.startswith("USERNAME="):
                        return line.strip().split("=", 1)[1]
        return None

    def delete_env(self) -> None:
        with self._lock:
            try:
                os.remove(self.env_path)
            except FileNotFoundError:
                pass
