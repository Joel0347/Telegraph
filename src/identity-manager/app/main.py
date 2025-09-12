from flask import Flask, request, jsonify
from auth import login_user, hash_password
from database import save_users

app = Flask(__name__)

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Faltan datos"}), 400

        # Aquí iría tu lógica de registro, por ejemplo guardar en archivo o base de datos
        save_users({username: {'password': hash_password(password), 'messages': []}})
        return jsonify({"message": f"Usuario {username} registrado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(data.get("username"), data.get("password"))
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
