import json
import hashlib
from database import load_users

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = users.get(username)
    
    if user and user.get("password") == hashed:
        return {'status': 'success', 'message': 'Login exitoso'}
    
    return {'status': 'error', 'message': 'Credenciales inválidas'}