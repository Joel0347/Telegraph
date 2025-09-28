import os
import logging
from flask import Flask, request, jsonify
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
_repo = MessageRepository()
_service = MessageService(_repo)

@app.post("/notify_read")
def notify_read():
    data = request.get_json(silent=True) or {}
    fr = data.get("from")
    to = data.get("to")
    if not fr or not to:
        return jsonify({"error": "payload inválido"}), 400
    local_user = os.getenv("USERNAME")
    if local_user and to != local_user:
        return jsonify({"error": "usuario destino incorrecto"}), 403
    changed = _service.mark_sent_messages_as_read(local_user, fr)
    return jsonify({"marked": changed}), 200

@app.post("/receive_message")
def receive_message():
    data = request.get_json(silent=True) or {}
    sender = data.get("from")
    receiver = data.get("to")
    text = data.get("text")

    if not sender or not receiver or not text:
        return jsonify({"error": "payload inválido"}), 400

    local_user = os.getenv("USERNAME")
    if local_user and receiver != local_user:
        return jsonify({"error": "destinatario incorrecto"}), 403

    _service.save_message(sender, receiver, text, sended=False)
    logging.info(f"Mensaje recibido de {sender} para {receiver}")
    return jsonify({"status": "ok"}), 200

def start_flask_server():
    port = int(os.getenv("API_PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
