from flask import request, jsonify
import hashlib
from database import load_users, save_users

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str):
    try:
        if not username or not password:
            return jsonify({"error": "Faltan datos"}), 400
        
        users = load_users()
        # Buscar si el usuario ya existe
        if any(u["username"] == username for u in users):
            return {"message": f"Usuario {username} ya se encuentra registrado", "status": 409}

        users.append({
            "username": username,
            "password": hash_password(password),
            "messages": []
        })
        save_users(users)
        return {"message": f"Usuario {username} registrado correctamente", "status": 200}

    except Exception as e:
        return jsonify({"error": str(e), "status": 500})
    

def login_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = next((u for u in users if u["username"] == username), None)
    if user and user.get("password") == hashed:
        return {"status": 200, "message": 'Login exitoso'}
    return {"status": 500, "message": 'Credenciales inválidas'}