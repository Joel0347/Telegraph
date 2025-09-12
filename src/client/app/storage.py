import json
import os

STORAGE_PATH = "app/messages.json"

def load_messages():
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, "r") as f:
        return json.load(f)

def save_message(sender, receiver, text):
    messages = load_messages()
    chat_id = f"{sender}_{receiver}"
    if chat_id not in messages:
        messages[chat_id] = []
    messages[chat_id].append({"from": sender, "to": receiver, "text": text})
    with open(STORAGE_PATH, "w") as f:
        json.dump(messages, f)