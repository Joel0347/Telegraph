import socket
import threading
import json
from storage import save_message

def handle_connection(conn, addr):
    data = conn.recv(4096).decode()
    try:
        msg = json.loads(data)
        save_message(msg["from"], msg["to"], msg["text"])
        print(f"[RECEIVED] {msg['from']} → {msg['to']}: {msg['text']}")

        # Crear archivo de trigger
        trigger_path = f"/data/trigger_{msg['to']}.flag"
        with open(trigger_path, "w") as f:
            f.write("1")
    except Exception as e:
        print(f"Error al procesar mensaje: {e}")
    finally:
        conn.close()


def start_listener(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[LISTENER] Activo en {host}:{port}")

    def loop():
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()

    threading.Thread(target=loop, daemon=True).start()
