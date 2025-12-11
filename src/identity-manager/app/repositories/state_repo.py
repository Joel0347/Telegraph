import json
import os
from threading import Lock
from typing import List
from models.state import State


class StateRepository:
    _instance = None
    dbpath: str = None
    _lock: Lock = None
    
    def __new__(cls, dbpath=os.path.join('/data', 'status.json')):
        if cls._instance is None:
            cls._instance = super(StateRepository, cls).__new__(cls)
            cls._instance._lock = Lock()
            cls._instance.dbpath = os.path.abspath(dbpath)

            if not os.path.exists(cls._instance.dbpath):
                os.makedirs(os.path.dirname(cls._instance.dbpath), exist_ok=True)
                with open(cls._instance.dbpath, 'w', encoding='utf-8') as f:
                    json.dump(State().model_dump(), f, indent=2, ensure_ascii=False)
        return cls._instance


    def _read_all(self) -> dict:
        if not os.path.exists(self.dbpath):
            return {}
        with open(self.dbpath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, data: dict):
        with open(self.dbpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self) -> State:
        with self._lock:
            raw = self._read_all()
        return State(**raw)

    def update_state(self, state: State):
        with self._lock:
            raw = state.model_dump(mode="json")
            self._write_all(raw)
            
    def reset(self):
        with self._lock:
            self._write_all([])
