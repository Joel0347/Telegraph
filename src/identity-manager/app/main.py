from flask import Flask, request, jsonify
from auth import login_user, register_user

app = Flask(__name__)

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    ip = data.get("ip", "")
    port = data.get("port", 0)
    return register_user(username, password, ip, port)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    ip = data.get("ip", "")
    port = data.get("port", 0)
    return login_user(username, password, ip, port)

@app.route('/peers', methods=['GET'])
def get_peers():
    from database import load_users
    users = load_users()
    return jsonify([
        {"username": u["username"], "ip": u.get("ip", ""), "port": u.get("port", 0)}
        for u in users if u.get("ip") and u.get("port")
    ])


@app.route('/users', methods=['GET'])
def list_users():
    from database import load_users
    users = load_users()
    # No enviar contraseñas
    return jsonify([
        {"username": u["username"]} for u in users
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
