from flask import Flask, request, jsonify
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from requests.exceptions import RequestException, ConnectionError
import requests


app = Flask(__name__)
user_repo = UserRepository()
auth_service = AuthService(user_repo)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    msg = auth_service.register_user(
        username=data.get("username", ""),
        password=data.get("password", ""),
        ip=data.get("ip", ""),
        port=data.get("port", 0),
    )
    return jsonify(msg)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    msg = auth_service.login_user(
        username=data.get("username", ""),
        password=data.get("password", ""),
        ip=data.get("ip", ""),
        port=data.get("port", 0),
    )
    return jsonify(msg)

@app.route("/logout", methods=["POST"])
def logout():
    data = request.get_json(force=True)
    username = data.get("username", "")
    msg = auth_service.update_status(username=username, status="offline")
    return jsonify(msg)

@app.route("/peers", methods=["GET"])
def get_peers():
    peers = auth_service.get_peers()
    return jsonify({"peers": peers, "status": 200})

@app.route("/users", methods=["GET"])
def list_users():
    usernames = auth_service.list_usernames()
    return jsonify({"usernames": usernames, "status": 200})

@app.route("/users/<username>", methods=["GET"])
def find_by_username(username: str):
    msg = auth_service.get_user_by_username(username)
    return jsonify(msg)

@app.route("/users/status/<username>", methods=["POST"])
def notify_online(username: str):
    msg = auth_service.update_status(username, "online")
    return jsonify(msg)

@app.post("/heartbeat")
def heartbeat():
    """
    Endpoint que los clientes llaman periódicamente para indicar que siguen activos.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username")

    if not username:
        return jsonify({"message": "username requerido", "status": 400})

    try:
        auth_service.update_last_seen(username)
        return jsonify({"message": "heartbeat recibido", "status": 200})
    except Exception as e:
        return jsonify({"message": str(e), "status": 500})
    
@app.route("/users/active/<username>", methods=["GET"])
def is_user_active(username: str):
    msg = auth_service.get_user_by_username(username)
    
    if msg["status"] == 500:
        return jsonify(msg)
    
    return jsonify({"message": msg["message"]["status"], "status": 200})


# --- Job en background ---
def check_inactive_users():
    try:
        now = datetime.now()
        timeout = timedelta(seconds=30)  # tolerancia 1 minuto
        users = auth_service.list_all()
        for u in users:
            if u.last_seen and (now - u.last_seen) > timeout and u.status != "offline":
                auth_service.update_status(u.username, "offline")
                requests.post(f"http://{u.ip}:{u.port}/disconnect")
                app.logger.info(f"Usuario {u.username} marcado como offline por inactividad")
    except (Exception, ConnectionError, RequestException):
        app.logger.info(f"Usuario {u.username} ya está desconectado")
            
# --- Inicializar scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_inactive_users, trigger="interval", seconds=30)
scheduler.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
