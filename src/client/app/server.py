import os, logging
from flask import Flask, request, jsonify
from services.msg_service import MessageService
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService
from repositories.msg_repo import MessageRepository

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
msg_repo = MessageRepository()
api_srv = ApiHandlerService()
msg_srv = MessageService(msg_repo, api_srv)
client_srv = ClientInfoService()

@app.post("/notify_read")
def notify_read():
    data = request.get_json(silent=True) or {}
    fr = data.get("from")
    to = data.get("to")
    if not fr or not to:
        return jsonify({"error": "payload inválido"}), 400
    local_user = client_srv.get_username()
    if local_user and to != local_user:
        return jsonify({"error": "usuario destino incorrecto"}), 403
    changed = msg_srv.mark_sent_messages_as_read(local_user, fr)
    return jsonify({"marked": changed}), 200

@app.post("/receive_message")
def receive_message():
    data = request.get_json(silent=True) or {}
    sender = data.get("from")
    receiver = data.get("to")
    text = data.get("text")

    if not sender or not receiver or not text:
        return jsonify({"error": "payload inválido"}), 400

    local_user = client_srv.get_username()
    if local_user and receiver != local_user:
        return jsonify({"error": "destinatario incorrecto"}), 403

    msg_srv.save_message(sender, receiver, text, status="ok", sent=False)
    logging.info(f"Mensaje recibido de {sender} para {receiver}")
    return jsonify({"status": "ok"}), 200

@app.post("/disconnect")
def disconnect_user():
    try:
        client_srv.remove_username()
        return jsonify({"status": "ok"}), 200
    except:
        return jsonify({"status": "error"}), 200

@app.post("/new_leader/<leader_addr>")
def new_leader(leader_addr: str):
    try:
        api_srv.update_leader_addr(leader_addr)
        return jsonify({"status": "ok"}), 200
    except:
        return jsonify({"status": "error"}), 500
    
@app.post("/duplicated-session")
def duplicated_session():
    api_srv.set_duplicated_session(True)
    return jsonify({"status": "ok"}), 200

def start_flask_server():
    port = int(os.getenv("API_PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
