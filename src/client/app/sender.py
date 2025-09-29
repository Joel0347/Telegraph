import requests
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository
from shared import API_URL

_repo = MessageRepository()
_service = MessageService(_repo)

def send_message(sender: str, receiver: str, text: str):
    res = requests.get(f"{API_URL}/users/{receiver}")
    print(res.json())
    user = {}
    if res.json()["status"] == 200:
        user = res.json()["message"]
    else:
        raise ValueError(res.json()["message"])
    
    status = "ok" if user["status"] == "online" else "pending"
    _service.save_message(sender, receiver, text, status, sent=True)
    
    if status == "ok":
        ip, port = _service.get_peer_address(receiver)
        url = f"http://{ip}:{port}/receive_message"
        payload = {"from": sender, "to": receiver, "text": text}
        try:
            r = requests.post(url, json=payload, timeout=3)
            r.raise_for_status()
            print(f"Mensaje enviado a {receiver}")
        except Exception as e:
            print(f"Error enviando mensaje a {receiver}: {e}")


