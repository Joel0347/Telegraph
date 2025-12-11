from flask import Flask, request, jsonify
from services.auth_service import AuthService
from services.manager_service import ManagerService
from repositories.user_repo import UserRepository
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from requests.exceptions import RequestException, ConnectionError
import requests, threading
from udp_discovery import run_server
from dispatcher import Dispatcher


app = Flask(__name__)
user_repo = UserRepository()
auth_service = AuthService(user_repo)
dispatcher = Dispatcher(auth_service)
mng_service = ManagerService(dispatcher)

lock = threading.Lock()
blocked = False

# --- Interceptor ---
@app.before_request
def intercept_requests():
    global blocked
    
    allowed_when_blocked = ["list_users_info", "block_api", "reset", "status"]
    
    if request.endpoint in allowed_when_blocked:
        return None
    
    with lock:
        if blocked:
            return jsonify({"message": f"Reconectando ...", "status": 404})

    # Endpoints de clientes (los que definiste en la sección CLIENT ENDPOINTS)
    client_endpoints = {
        "register",
        "login",
        "logout",
        "notify_online",
        "heartbeat",
        "update_ip_address",
    }

    endpoint = request.endpoint  # nombre de la función de vista

    if endpoint in client_endpoints:
        # Extraer argumentos de la ruta y del body
        args = {}
        if request.view_args:  # parámetros de la URL
            args.update(request.view_args)
        if request.is_json:    # parámetros del body
            args.update(request.get_json(silent=True) or {})

        # Llamar a handle_client (asumimos que existe)
        response = mng_service.handle_client_request(endpoint, args)
        
        if not response["success"] and (leader := response.get("leader")):
            try:
                forward_url = f"http://{leader}:8000/" + request.path.lstrip("/")
                forwarded = requests.request(
                    method=request.method,
                    url=forward_url,
                    json=args,
                    timeout=10
                )
                return jsonify(forwarded.json())
            except Exception as e:
                return jsonify({
                    "message": f"No se pudo reenviar al líder {leader}: {str(e)}",
                    "status": 500
                })
        elif not response["success"]:
            # Bloquear ejecución del endpoint
            return jsonify({"message": f"Error: {response['message']}", "status": 500})

    # Si handle_client devolvió True → se ejecuta el endpoint normalmente
    return None

# -------------- CLIENT ENDPOINTS ------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    return dispatcher.register(data)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    return dispatcher.login(data)

@app.route("/logout", methods=["POST"])
def logout():
    data = request.get_json(force=True)
    return dispatcher.logout(data)

@app.route("/peers", methods=["GET"])
def get_peers():
    return dispatcher.get_peers()

@app.route("/users", methods=["GET"])
def list_users():
    return dispatcher.list_users()

@app.route("/users/<username>", methods=["GET"])
def find_by_username(username: str):
    data = {"username": username}
    return dispatcher.find_by_username(data)

@app.route("/users/status/<username>", methods=["POST"])
def notify_online(username: str):
    data = {"username": username}
    return dispatcher.notify_online(data)

@app.post("/heartbeat")
def heartbeat():
    """
    Endpoint que los clientes llaman periódicamente para indicar que siguen activos.
    """
    data = request.get_json(silent=True) or {}
    return dispatcher.heartbeat(data)
    
@app.route("/users/active/<username>", methods=["GET"])
def is_user_active(username: str):
    data = {"username": username}
    return dispatcher.is_user_active(data)

@app.route("/users/reconnect/<ip>/<username>", methods=["PUT"])
def update_ip_address(ip: str, username: str):
    data = {
        "username": username,
        "ip": ip
    }
    return dispatcher.update_ip_address(data)

# ------------ REPLICAS ENDPOINTS ------------------
@app.route('/request_vote', methods=['POST'])
def request_vote():
    data = request.json
    response = mng_service.handle_request_vote(data)
    return jsonify(response)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "node_id": mng_service._node_id,
        "state": mng_service._status.value,
        "current_term": mng_service._current_term,
        "commit_index": mng_service._commit_index,
        "log_length": len(mng_service._log),
        "peers": list(mng_service._managers_ips)
    })
    
@app.route('/append_entries', methods=['POST'])
def append_entries():
    mng_service.update_leader(request.remote_addr)
    data = request.json
    response = mng_service.handle_append_entries(data)
    return jsonify(response)
        
@app.post("/managers/new/<ip>")
def add_new_manager(ip: str):
    msg = mng_service.add_new_manager(ip)
    return jsonify(msg)

@app.get("/managers/leader")
def find_leader():
    msg = mng_service.get_leader()
    return jsonify(msg)

@app.post("/new_leader/<ip>")
def new_leader(ip: str):
    msg = mng_service.update_leader(ip)
    return jsonify(msg)

@app.route("/users/info", methods=["GET"])
def list_users_info():
    return dispatcher.list_all_users_data()

@app.post("/block")
def block_api():
    global blocked
    
    with lock:
        if not blocked and mng_service._election_timer:
            mng_service._election_timer.cancel()
        elif blocked:
            mng_service.reset_election_timer()
        blocked = not blocked
    
    return jsonify({"message": f"Status: {blocked}", "status": 200})

@app.post("/reset")
def reset():
    mng_service.reset()
    return jsonify({"message": "Reiniciado exitosamente", "status": 200})
        
# --- Job en background ---
def check_inactive_users():
    if not mng_service.I_am_leader():
        return
    
    try:
        now = datetime.now()
        timeout = timedelta(seconds=60)  # tolerancia 60 seg
        users = auth_service.list_all()
        for u in users:
            if u.last_seen and (now - u.last_seen) > timeout and u.status != "offline":
                auth_service.update_status(u.username, "offline")
                args = {"username": u.username}
                mng_service.handle_client_request("update_status", args)
                requests.post(f"http://{u.ip}:{u.port}/disconnect")
                app.logger.info(f"Usuario {u.username} marcado como offline por inactividad")
    except (Exception, ConnectionError, RequestException):
        app.logger.info(f"Usuario {u.username} ya está desconectado")
            
# --- Inicializar scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_inactive_users, trigger="interval", seconds=30)
scheduler.start()


if __name__ == "__main__":
    # lanzar el servidor UDP en un hilo
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8000)
