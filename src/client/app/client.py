import json
import socket
import requests
from datetime import datetime
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository

_repo = MessageRepository()
_service = MessageService(_repo)

def send_message(sender: str, receiver: str, text: str) -> str:
    _service.save_message(sender, receiver, text)

    ip, port = _get_peer_address(receiver)
    if not ip or not port:
        return f"No se encontró IP/puerto de {receiver}"

    msg = {
        "from": sender,
        "to": receiver,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((ip, port))
        _socket.sendall(json.dumps(msg).encode())
        _socket.close()
        return f"Mensaje enviado a {receiver} vía red"
    except Exception as e:
        return f"Error al enviar a {receiver}: {e}"

def get_chat(user: str, other: str) -> list[dict]:
    messages = _service.load_conversations(user).get(other, [])
    return [m.to_json_dict() for m in sorted(messages, key=lambda m: m.timestamp)]

def mark_chat_as_read(user: str, from_user: str) -> int:
    return _service.mark_as_read(user, from_user)

def unread_count(user: str, from_user: str | None = None) -> int:
    return _service.unread_count(user, from_user)

def _get_peer_address(username: str):
    try:
        res = requests.get("http://identity-manager:8000/peers", timeout=2)
        res.raise_for_status()
        peers = res.json().get("peers", [])
        peer = next((p for p in peers if p["username"] == username), None)
        if peer:
            return peer.get("ip"), peer.get("port")
    except Exception:
        pass
    return None, None
