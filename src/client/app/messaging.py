import json
import socket
import requests
from storage import save_message, load_messages
from datetime import datetime


def send_message(sender, receiver, text):
    
    save_message(sender, receiver, text)

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

def get_chat(user, other):
    messages = load_messages(user)
    chat_msgs = messages.get(other, [])
    chat_msgs.sort(key=lambda m: m.get("timestamp", ""))
    return chat_msgs

def _get_peer_address(username):
    try:
        res = requests.get("http://identity-manager:8000/peers")
        peers = res.json()
        peer = next((p for p in peers if p["username"] == username), None)
        if peer:
            return peer["ip"], peer["port"]
    except:
        pass
    return None, None