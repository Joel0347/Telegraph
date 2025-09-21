from storage import save_message, load_messages

def send_message(sender, receiver, text):
    save_message(sender, receiver, text)
    return f"Mensaje enviado de {sender} a {receiver}"

def get_chat(user, other):
    messages = load_messages(user)
    chat_msgs = messages.get(other, [])
    # Ordenar por timestamp
    chat_msgs.sort(key=lambda m: m.get("timestamp", ""))
    return chat_msgs