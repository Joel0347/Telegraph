from repositories.log_repo import LogRepository
from models.log import Log


class LogService:
    _instance = None
    repo: LogRepository = None
    
    def __new__(cls, repo: LogRepository):
        if cls._instance is None:
            cls._instance = super(LogService, cls).__new__(cls)
            cls._instance.repo = repo
        return cls._instance


    def add_log(self, payload: dict) -> dict:
        try:
            log = Log(
                term=payload['term'],
                index=payload['index'],
                op=payload['op'],
                args=payload['args'],
                applied=payload['applied']
            )
            self.repo.add_log(log)
            return {"message": 'Log agregado exitosamente', "status": 200}

        except Exception as e:
            return {"message": str(e), "status": 500}
        
        
    def update_applied(self, index: int, applied: bool):
        try:
            log = self.repo.find_by_index(index)
            log.applied = applied
            self.repo.update_log(log)
            return {"message": 'Log actualizado exitosamente', "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}
    
    def list_all(self) -> list[Log]:
        return self.repo.list_all()
    
    def find_by_index(self, index: int) -> dict:
        try:
            log = self.repo.find_by_index(index)
            return {"message": log.model_dump(mode="json"), "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}