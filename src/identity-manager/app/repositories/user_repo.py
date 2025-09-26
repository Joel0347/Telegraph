import json
import os
from threading import Lock
from typing import List, Optional
from models.user import User


class UserRepository:
    def __init__(self, dbpath=os.path.join('/data', 'users.json')):
        self._lock = Lock()
        self.dbpath = os.path.abspath(dbpath)

        if not os.path.exists(self.dbpath):
            os.makedirs(os.path.dirname(self.dbpath), exist_ok=True)
            with open(self.dbpath, 'w', encoding='utf-8') as f:
                f.write('[]')


    def _read_all(self) -> List[dict]:
        if not os.path.exists(self.dbpath):
            return []
        with open(self.dbpath, "r", encoding="utf-8") as f:
            return json.load(f)


    def _write_all(self, data: List[dict]):
        with open(self.dbpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def list_all(self) -> List[User]:
        with self._lock:
            raw = self._read_all()
        return [User(**u) for u in raw]


    def find_by_username(self, username: str) -> Optional[User]:
        with self._lock:
            raw = self._read_all()
        for u in raw:
            if u.get("username") == username:
                return User(**u)
        return None


    def add_user(self, user: User):
        with self._lock:
            raw = self._read_all()
            if any(u.get("username") == user.username for u in raw):
                raise ValueError("Usuario ya existe")
            raw.append(user.model_dump())
            self._write_all(raw)


    def update_user(self, user: User):
        with self._lock:
            raw = self._read_all()
            for i, u in enumerate(raw):
                if u.get("username") == user.username:
                    raw[i] = user.model_dump()
                    self._write_all(raw)
                    return
            raise ValueError("Usuario no existe")
