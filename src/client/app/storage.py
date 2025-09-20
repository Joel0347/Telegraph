import json
import os
from datetime import datetime

STORAGE_PATH = "messages.json"

def mark_messages_as_read(user, from_user):
    """
    Marca como leídos todos los mensajes enviados a 'user' por 'from_user'.
    """
    if not os.path.exists(STORAGE_PATH):
        return
    with open(STORAGE_PATH, "r") as f:
        all_msgs = json.load(f)
    changed = False
    for msg in all_msgs:
        if msg["from"] == from_user and msg["to"] == user and not msg.get("leido", False):
            msg["leido"] = True
            changed = True
    if changed:
        with open(STORAGE_PATH, "w") as f:
            json.dump(all_msgs, f, indent=2)

def load_messages(user):
    """
    Devuelve un diccionario {otro_usuario: [mensajes]} con todos los mensajes enviados o recibidos por 'user'.
    """
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, "r") as f:
        all_msgs = json.load(f)
    chats = {}
    for msg in all_msgs:
        if msg["from"] == user:
            other = msg["to"]
        elif msg["to"] == user:
            other = msg["from"]
        else:
            continue
        if other not in chats:
            chats[other] = []
        chats[other].append(msg)
    return chats

def save_message(sender, receiver, text):
    msg = {
        "from": sender,
        "to": receiver,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
        "leido": False
    }
    if not os.path.exists(STORAGE_PATH):
        all_msgs = []
    else:
        with open(STORAGE_PATH, "r") as f:
            all_msgs = json.load(f)
    all_msgs.append(msg)
    with open(STORAGE_PATH, "w") as f:
        json.dump(all_msgs, f, indent=2)