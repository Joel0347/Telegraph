import requests
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository

_repo = MessageRepository()
_service = MessageService(_repo)

def send_message(sender: str, receiver: str, text: str):
    _service.save_message(sender, receiver, text, sended=True)
    ip, port = _service.get_peer_address(receiver)
    url = f"http://{ip}:{port}/receive_message"
    payload = {"from": sender, "to": receiver, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=3)
        r.raise_for_status()
        print(f"Mensaje enviado a {receiver}")
    except Exception as e:
        print(f"Error enviando mensaje a {receiver}: {e}")


