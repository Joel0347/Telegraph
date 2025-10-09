import os
import json
from threading import Lock
from typing import List
from models.message import Message
from models.msg_group import MessageGroup


class MessageRepository:
    _instance = None
    base_folder: str = None
    _lock: Lock = None

    def __new__(cls, base_folder=os.path.join("/data", "messages")):
        if cls._instance is None:
            cls._instance = super(MessageRepository, cls).__new__(cls)
            cls._instance._lock = Lock()
            cls._instance.base_folder = base_folder
            os.makedirs(cls._instance.base_folder, exist_ok=True)
        return cls._instance

    def _path_for(self, user_id: str) -> str:
        return os.path.join(self.base_folder, f"messages_{user_id}.json")

    def _read_all(self, path: str) -> List[MessageGroup]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            try:
                raw = json.load(f)
                return [MessageGroup.model_validate(g) for g in raw]
            except json.JSONDecodeError:
                return []
            except Exception:
                return []

    def _write_all(self, path: str, groups: List[MessageGroup]):
        raw = [g.model_dump(by_alias=True, mode="json") for g in groups]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)

    def load(self, user_id: str) -> List[MessageGroup]:
        """
        Devuelve la lista de grupos de mensajes de un usuario.
        """
        path = self._path_for(user_id)
        with self._lock:
            return self._read_all(path)

    def save(self, user_id: str, groups: List[MessageGroup]):
        """
        Guarda la lista completa de grupos de mensajes de un usuario.
        """
        path = self._path_for(user_id)
        with self._lock:
            self._write_all(path, groups)

    def set_group_synchronized(self, user_id: str, other: str, synchronized: bool):
        """
        Actualiza el campo 'synchronized' del grupo con 'other' en el archivo de user_id.
        """
        path = self._path_for(user_id)
        with self._lock:
            groups = self._read_all(path)
            for g in groups:
                if g.name == other:
                    g.synchronized = synchronized
                    break
            self._write_all(path, groups)
            
    def get_unsynchronized_groups(self, user_id: str) -> List[str]:
        """
        Devuelve los nombres de los grupos que están marcados como no sincronizados.
        """
        path = self._path_for(user_id)
        with self._lock:
            groups = self._read_all(path)
            return [g.name for g in groups if not g.synchronized]


    def append_message(self, user_id: str, other: str, message: Message):
        """
        Añade un mensaje al grupo correspondiente (crea el grupo si no existe).
        """
        path = self._path_for(user_id)
        with self._lock:
            groups = self._read_all(path)
            # buscar grupo existente
            group = next((g for g in groups if g.name == other), None)
            if not group:
                group = MessageGroup(name=other, messages=[])
                groups.append(group)
            group.messages.append(message)
            self._write_all(path, groups)

    def mark_messages_from_as_read(self, user_id: str, from_user: str) -> int:
        """
        Marca como leídos los mensajes recibidos de from_user.
        """
        path = self._path_for(user_id)
        changed = 0
        with self._lock:
            groups = self._read_all(path)
            for g in groups:
                if g.name == from_user:
                    for m in g.messages:
                        if m.from_ == from_user and m.to == user_id and not m.read:
                            m.read = True
                            changed += 1
            if changed:
                self._write_all(path, groups)
        return changed

    def mark_messages_sent_to_as_read(self, user_id: str, to_user: str) -> int:
        """
        Marca como leídos los mensajes que user_id envió a to_user.
        """
        path = self._path_for(user_id)
        changed = 0
        with self._lock:
            groups = self._read_all(path)
            for g in groups:
                if g.name == to_user:
                    for m in g.messages:
                        if m.from_ == user_id and m.to == to_user and not m.read:
                            m.read = True
                            changed += 1
            if changed:
                self._write_all(path, groups)
        return changed

    def update_message_status(self, user_id: str, other: str, timestamp: str, new_status: str) -> bool:
        """
        Actualiza el campo 'status' de un mensaje específico en el grupo con 'other'.
        """
        path = self._path_for(user_id)
        updated = False
        with self._lock:
            groups = self._read_all(path)
            for g in groups:
                if g.name == other:
                    for m in g.messages:
                        if str(m.timestamp) == timestamp:
                            m.status = new_status
                            updated = True
                            break
            if updated:
                self._write_all(path, groups)
        return updated
