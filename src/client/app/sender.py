import requests
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository
from services.api_handler_service import ApiHandlerService


msg_repo = MessageRepository()
api_srv = ApiHandlerService()
msg_srv = MessageService(msg_repo, api_srv)

def send_message(sender: str, receiver: str, text: str):
    user = api_srv.get_user_by_username(receiver)
    status = "ok" if user["status"] == "online" else "pending"
    
    if status == "ok":
        ip, port = api_srv.get_peer_address(receiver)
        url = f"http://{ip}:{port}/receive_message"
        payload = {"from": sender, "to": receiver, "text": text}
        try:
            r = requests.post(url, json=payload, timeout=3)
            r.raise_for_status()
            print(f"Mensaje enviado a {receiver}")
        except Exception as e:
            status = "pending"
            print(f"Error enviando mensaje a {receiver}: {e}")
    
    msg_srv.save_message(sender, receiver, text, status, sent=True)



