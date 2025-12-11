import json
import os
from threading import Lock
from typing import List
from models.log import Log


class LogRepository:
    _instance = None
    dbpath: str = None
    _lock: Lock = None
    
    def __new__(cls, dbpath=os.path.join('/data', 'log.json')):
        if cls._instance is None:
            cls._instance = super(LogRepository, cls).__new__(cls)
            cls._instance._lock = Lock()
            cls._instance.dbpath = os.path.abspath(dbpath)

            if not os.path.exists(cls._instance.dbpath):
                os.makedirs(os.path.dirname(cls._instance.dbpath), exist_ok=True)
                with open(cls._instance.dbpath, 'w', encoding='utf-8') as f:
                    f.write('[]')
        return cls._instance


    def _read_all(self) -> List[dict]:
        if not os.path.exists(self.dbpath):
            return []
        with open(self.dbpath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, data: List[dict]):
        with open(self.dbpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_all(self) -> List[Log]:
        with self._lock:
            raw = self._read_all()
        return [Log(**u) for u in raw]

    def find_by_index(self, index: int) -> Log:
        logs = self.list_all()
        for log in logs:
            if log.index == index:
                return log
        raise ValueError("Log no existe")
    
    def find_by_applied_criteria(self, applied: bool) -> List[Log]:
        logs = self.list_all()
        return [log for log in logs if log.applied == applied]

    def add_log(self, log: Log):
        with self._lock:
            raw = self._read_all()
            if any(l.get("index") == log.index for l in raw):
                raise ValueError("Log ya existe")
            
            raw.append(log.model_dump(mode="json"))
            self._write_all(raw)
    
    # En LogRepository
    def add_logs_batch(self, logs: list[Log]):
        with self._lock:
            raw = self._read_all()
            for log in logs:
                if any(l.get("index") == log.index for l in raw):
                    raise ValueError(f"Log ya existe: index={log.index}")
                raw.append(log.model_dump(mode="json"))
            self._write_all(raw)

            
    def delete_log_by_index(self, index: int):
        logs = self.list_all()
        data = [log.model_dump(mode="json") for log in logs if log.index != index]
        self._write_all(data)

    def update_log(self, log: Log):
        with self._lock:
            raw = self._read_all()
            for i, l in enumerate(raw):
                if l.get("index") == log.index:
                    raw[i] = log.model_dump(mode="json")
                    self._write_all(raw)
                    return
            raise ValueError("Log no existe")

    def reset(self):
        with self._lock:
            self._write_all([])
