from storage import save_message, load_messages

def send_message(sender, receiver, text):
    save_message(sender, receiver, text)
    return f"Mensaje enviado de {sender} a {receiver}"

def get_chat(sender, receiver):
    messages = load_messages(sender)
    chat_msgs = []
    # Tomar todos los mensajes entre sender y receiver
    for msg in messages.get(receiver, []):
        if (msg["from"] == sender and msg["to"] == receiver) or (msg["from"] == receiver and msg["to"] == sender):
            chat_msgs.append(msg)
    # Ordenar por timestamp
    chat_msgs.sort(key=lambda m: m.get("timestamp", ""))
    return chat_msgs