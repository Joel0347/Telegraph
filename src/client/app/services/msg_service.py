import requests
from typing import List, Literal, Optional
from datetime import datetime
from models.message import Message
from models.msg_group import MessageGroup
from repositories.msg_repo import MessageRepository
from services.api_handler_service import ApiHandlerService


class MessageService:
    _instance = None
    repo: MessageRepository = None
    api_srv: ApiHandlerService = None

    def __new__(cls, repo: MessageRepository, api_srv: ApiHandlerService):
        if cls._instance is None:
            cls._instance = super(MessageService, cls).__new__(cls)
            cls._instance.repo = repo
            cls._instance.api_srv = api_srv
        return cls._instance

    def save_message(
        self, sender: str, receiver: str, text: str,
        status: Literal["ok", "pending"], sent: bool
    ) -> Message:
        msg = Message(
            from_=sender,
            to=receiver,
            text=text,
            timestamp=datetime.utcnow(),
            read=False,
            status=status
        )
        
        if sent:
            self.repo.append_message(sender, receiver, msg)
        else:
            self.repo.append_message(receiver, sender, msg)
        return msg

    def update_msg_status(
        self, sender: str, receiver: str,
        timestamp: str, status: Literal["ok", "pending"]
    ) -> bool:
        return self.repo.update_message_status(sender, receiver, timestamp, status)

    def load_conversations(self, user: str) -> List[MessageGroup]:
        return self.repo.load(user)

    def get_chat(self, user: str, other: str) -> List[Message]:
        groups = self.load_conversations(user)
        group = next((g for g in groups if g.name == other), None)
        return sorted(group.messages, key=lambda m: m.timestamp) if group else []

    def _notify_read_receipt(self, sender: str, receiver: str) -> bool:
        ip, port = self.api_srv.get_peer_address(sender)
        if not ip or not port:
            return False
        try:
            url = f"http://{ip}:{port}/notify_read"
            payload = {"from": receiver, "to": sender}
            r = requests.post(url, json=payload, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def send_message(
        self, sender: str, receiver: str, text: str,
        timestamp: Optional[str] = None, retried: bool = False
    ):
        user = self.api_srv.get_user_by_username(receiver)
        status: Literal["ok", "pending"] = "ok" if user["status"] == "online" else "pending"

        if status == "ok":
            ip, port = self.api_srv.get_peer_address(receiver)
            url = f"http://{ip}:{port}/receive_message"
            payload = {"from": sender, "to": receiver, "text": text}
            try:
                r = requests.post(url, json=payload, timeout=3)
                r.raise_for_status()
                print(f"Mensaje enviado a {receiver}")
            except Exception as e:
                status = "pending"
                print(f"Error enviando mensaje a {receiver}: {e}")

        if not retried:
            self.save_message(sender, receiver, text, status, sent=True)
        else:
            self.update_msg_status(sender, receiver, timestamp, status)

    def mark_as_read(self, user: str, from_user: str) -> int:
        changed = self.repo.mark_messages_from_as_read(user, from_user)
        if changed:
            self._notify_read_receipt(from_user, user)
        return changed

    def mark_sent_messages_as_read(self, user: str, to_user: str) -> int:
        return self.repo.mark_messages_sent_to_as_read(user, to_user)

    def unread_count(self, user: str, from_user: Optional[str] = None) -> int:
        groups = self.repo.load(user)
        total = 0
        if from_user:
            group = next((g for g in groups if g.name == from_user), None)
            msgs = group.messages if group else []
            total = sum(1 for m in msgs if not m.read and m.to == user)
        else:
            for g in groups:
                total += sum(1 for m in g.messages if not m.read and m.to == user)
        return total

    def find_pending_mssgs_by_user(self, username: str, users: List[str]) -> dict[str, List[Message]]:
        """
        Busca mensajes pendientes enviados por `username` a cada usuario en `users`.
        """
        pending_to_send: dict[str, List[Message]] = {}
        for other in users:
            chat_msgs = self.get_chat(username, other)
            if not chat_msgs:
                continue

            # Buscar el último mensaje enviado por el usuario actual
            last_idx = None
            for i in range(len(chat_msgs) - 1, -1, -1):
                if chat_msgs[i].from_ == username:
                    last_idx = i
                    break
            if last_idx is None:
                continue

            # Si el último mensaje enviado está pendiente
            if chat_msgs[last_idx].status == "pending":
                first_pending_idx = last_idx
                for i in range(last_idx, -1, -1):
                    if chat_msgs[i].from_ == username and chat_msgs[i].status == "pending":
                        first_pending_idx = i
                    elif chat_msgs[i].from_ == username:
                        break
                pending_to_send[other] = chat_msgs[first_pending_idx:last_idx + 1]
        return pending_to_send

    def send_pending_mssgs(self, pending_to_send: dict[str, List[Message]], username: str):
        for other, msgs in pending_to_send.items():
            for m in msgs:
                if m.status == "pending":
                    self.send_message(username, other, m.text, str(m.timestamp), retried=True)
