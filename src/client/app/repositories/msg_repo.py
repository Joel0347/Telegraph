import os
import json
from threading import Lock
from typing import Dict, List
from models.message import Message

class MessageRepository:
    def __init__(self, base_folder=os.path.join("/data", "messages")):
        self._lock = Lock()
        self.base_folder = base_folder
        os.makedirs(self.base_folder, exist_ok=True)

    def _path_for(self, user_id: str) -> str:
        return os.path.join(self.base_folder, f"messages_{user_id}.json")

    def _read_all(self, path: str) -> Dict[str, List[dict]]:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _write_all(self, path: str, data: Dict[str, List[dict]]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, user_id: str) -> Dict[str, List[Message]]:
        path = self._path_for(user_id)
        with self._lock:
            raw = self._read_all(path)
        out: Dict[str, List[Message]] = {}
        for other, msgs in raw.items():
            out[other] = []
            if isinstance(msgs, list):
                for m in msgs:
                    try:
                        out[other].append(Message.model_validate(m))
                    except Exception:
                        continue
        return out

    def save(self, user_id: str, groups: Dict[str, List[Message]]):
        path = self._path_for(user_id)
        raw = {
            other: [m.model_dump(by_alias=True) for m in msgs]
            for other, msgs in groups.items()
        }
        with self._lock:
            self._write_all(path, raw)

    def append_message(self, user_id: str, other: str, message: Message):
        path = self._path_for(user_id)
        with self._lock:
            raw = self._read_all(path)
            if other not in raw:
                raw[other] = []
            raw[other].append(message.model_dump(by_alias=True))
            self._write_all(path, raw)

    def mark_messages_from_as_read(self, user_id: str, from_user: str) -> int:
        path = self._path_for(user_id)
        changed = 0
        with self._lock:
            raw = self._read_all(path)
            if from_user in raw and isinstance(raw[from_user], list):
                for m in raw[from_user]:
                    if m.get("from") == from_user and m.get("to") == user_id and not m.get("read", False):
                        m["read"] = True
                        changed += 1
                if changed:
                    self._write_all(path, raw)
        return changed
