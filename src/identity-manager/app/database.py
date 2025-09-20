import json
import os

DB_PATH = 'users.json'

def load_users():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)