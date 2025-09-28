import requests
from typing import Dict, List, Optional
from datetime import datetime
from models.message import Message
from repositories.msg_repo import MessageRepository

class MessageService:
    def __init__(
        self, repo: MessageRepository,
        identity_manager_url="http://identity-manager:8000"
    ):
        self.repo = repo
        self.identity_manager_url = identity_manager_url

    def save_message(self, sender: str, receiver: str, text: str, sended: bool) -> Message:
        msg = Message(
            from_=sender,
            to=receiver,
            text=text,
            timestamp=datetime.utcnow().isoformat(),
            read=False
        )
        if sended:
            self.repo.append_message(sender, receiver, msg)
        else:
            self.repo.append_message(receiver, sender, msg)    
        return msg

    def load_conversations(self, user: str) -> Dict[str, List[Message]]:
        return self.repo.load(user)
    
    def get_chat(self, user: str, other: str) -> list[dict]:
        messages = self.load_conversations(user).get(other, [])
        return [
            m.model_dump(by_alias=True, mode="json") \
                for m in sorted(messages, key=lambda m: m.timestamp)
        ]

    def get_peer_address(self, username: str) -> Optional[tuple]:
        try:
            res = requests.get(f"{self.identity_manager_url}/peers", timeout=2)
            res.raise_for_status()
            peers = res.json().get("peers", [])
            peer = next((p for p in peers if p["username"] == username), None)
            if peer:
                return peer.get("ip"), peer.get("port")
        except Exception:
            return None
        return None

    def _notify_read_receipt(self, sender: str, receiver: str) -> bool:
        ip, port = self.get_peer_address(sender)
        if not ip or not port:
            return False
        try:
            url = f"http://{ip}:{port}/notify_read"
            payload = {"from": receiver, "to": sender}
            r = requests.post(url, json=payload, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def mark_as_read(self, user: str, from_user: str) -> int:
        changed = self.repo.mark_messages_from_as_read(user, from_user)
        if changed:
            self._notify_read_receipt(from_user, user)
        return changed
    
    def mark_sent_messages_as_read(self, user: str, to_user: str) -> int:
        """
        Marca en el repositorio local del *user* los mensajes que él envió a *to_user*.
        """
        return self.repo.mark_messages_sent_to_as_read(user, to_user)

    def unread_count(self, user: str, from_user: str | None = None) -> int:
        groups = self.repo.load(user)
        total = 0
        if from_user:
            msgs = groups.get(from_user, [])
            total = sum(1 for m in msgs if not m.read and m.to == user)
        else:
            for other, msgs in groups.items():
                total += sum(1 for m in msgs if not m.read and m.to == user)
        return total
