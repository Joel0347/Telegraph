from repositories.client_repo import ClientRepository


class ClientInfoService:
    _instance = None
    repo: ClientRepository = None

    def __new__(cls, repo: ClientRepository = None):
        if cls._instance is None:
            cls._instance = super(ClientInfoService, cls).__new__(cls)
            cls._instance.repo = repo or ClientRepository()
        return cls._instance

    def save_username(self, username: str):
        """
        Guarda el nombre de usuario en el archivo .env para persistencia local.
        """
        self.repo.save_username(username)

    def get_username(self) -> str | None:
        """
        Recupera el nombre de usuario desde el archivo .env si existe.
        """
        return self.repo.load_username()

    def remove_username(self):
        """
        Elimina el archivo .env para limpiar la sesión local.
        """
        self.repo.delete_env()
