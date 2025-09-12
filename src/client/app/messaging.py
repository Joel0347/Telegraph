from storage import save_message, load_messages

def send_message(sender, receiver, text):
    save_message(sender, receiver, text)
    return f"Mensaje enviado de {sender} a {receiver}"

def get_chat(sender, receiver):
    messages = load_messages()
    chat_id = f"{sender}_{receiver}"
    reverse_id = f"{receiver}_{sender}"
    chat = messages.get(chat_id, []) + messages.get(reverse_id, [])
    return sorted(chat, key=lambda m: m.get("timestamp", 0))  # si agregas timestamps