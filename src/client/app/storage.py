import json
import os
from datetime import datetime


def get_storage_path(user_id):
    """
    Devuelve la ruta del archivo de mensajes para un usuario específico.
    """
    return os.path.join("messages", f"messages_{user_id}.json")

def mark_messages_as_read(user, from_user):
    """
    Marca como leídos todos los mensajes enviados a 'user' por 'from_user'.
    """
    storage_path = get_storage_path(user)
    if not os.path.exists(storage_path):
        return
    with open(storage_path, "r") as f:
        try:
            chats = json.load(f)
        except json.JSONDecodeError:
            chats = {}
    changed = False
    # Marcar como leídos en el archivo del usuario que lee
    if from_user in chats:
        for msg in chats[from_user]:
            if msg["from"] == from_user and msg["to"] == user and not msg.get("leido", False):
                msg["leido"] = True
                changed = True
    if changed:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        with open(storage_path, "w") as f:
            json.dump(chats, f, indent=2)

    # También marcar como leídos en el archivo del remitente
    sender_path = get_storage_path(from_user)
    if os.path.exists(sender_path):
        with open(sender_path, "r") as f:
            try:
                sender_chats = json.load(f)
            except json.JSONDecodeError:
                sender_chats = {}
        sender_changed = False
        if user in sender_chats:
            for msg in sender_chats[user]:
                if msg["from"] == from_user and msg["to"] == user and not msg.get("leido", False):
                    msg["leido"] = True
                    sender_changed = True
        if sender_changed:
            os.makedirs(os.path.dirname(sender_path), exist_ok=True)
            with open(sender_path, "w") as f:
                json.dump(sender_chats, f, indent=2)

def load_messages(user):
    """
    Devuelve un diccionario {otro_usuario: [mensajes]} con todos los mensajes enviados o recibidos por 'user'.
    """
    storage_path = get_storage_path(user)
    if not os.path.exists(storage_path):
        return {}
    with open(storage_path, "r") as f:
        try:
            chats = json.load(f)
        except json.JSONDecodeError:
            chats = {}
    return chats

def save_message(sender, receiver, text):
    """
    Guarda el mensaje en el archivo del usuario sender y lo replica en el archivo del receiver.
    """
    msg = {
        "from": sender,
        "to": receiver,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
        "leido": False
    }
    # Guardar en archivo del sender
    sender_path = get_storage_path(sender)
    if not os.path.exists(sender_path):
        sender_chats = {}
    else:
        with open(sender_path, "r") as f:
            try:
                sender_chats = json.load(f)
            except json.JSONDecodeError:
                sender_chats = {}
    if receiver not in sender_chats:
        sender_chats[receiver] = []
    sender_chats[receiver].append(msg)
    os.makedirs(os.path.dirname(sender_path), exist_ok=True)
    with open(sender_path, "w") as f:
        json.dump(sender_chats, f, indent=2)

    # Guardar en archivo del receiver (replicado)
    receiver_path = get_storage_path(receiver)
    if not os.path.exists(receiver_path):
        receiver_chats = {}
    else:
        with open(receiver_path, "r") as f:
            try:
                receiver_chats = json.load(f)
            except json.JSONDecodeError:
                receiver_chats = {}
    if sender not in receiver_chats:
        receiver_chats[sender] = []
    # Marcar como no leído para el receiver
    msg_receiver = msg.copy()
    msg_receiver["leido"] = False
    receiver_chats[sender].append(msg_receiver)
    os.makedirs(os.path.dirname(receiver_path), exist_ok=True)
    with open(receiver_path, "w") as f:
        json.dump(receiver_chats, f, indent=2)