from flask import Flask, request, jsonify
from services.auth_service import AuthService
from repositories.user_repo import UserRepository

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

@app.route("/peers", methods=["GET"])
def get_peers():
    peers = auth_service.get_peers()
    return jsonify({"peers": peers, "status": 200})

@app.route("/users", methods=["GET"])
def list_users():
    usernames = auth_service.list_usernames()
    return jsonify({"usernames": usernames, "status": 200})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
