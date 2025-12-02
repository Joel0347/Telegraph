from repositories.state_repo import StateRepository


class StateService:
    _instance = None
    repo: StateRepository = None
    
    def __new__(cls, repo: StateRepository):
        if cls._instance is None:
            cls._instance = super(StateService, cls).__new__(cls)
            cls._instance.repo = repo
        return cls._instance
    
          
    def update(self, payload: dict) -> dict:
        try:
            state = self.repo.get()
            
            for key in payload:
                setattr(state, key, payload[key])
            
            self.repo.update_state(state)
            return {"message": 'Log actualizado exitosamente', "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}
    
    def load(self) -> dict:
        try:
            state = self.repo.get()
            return {"message": state.model_dump(mode="json"), "status": 200}
        except Exception as e:
            return {"message": str(e), "status": 500}