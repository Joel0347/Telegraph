import os
from flask import Flask, request, jsonify
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository

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

    changed = _service.mark_as_read(to, fr)
    return jsonify({"marked": changed}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
