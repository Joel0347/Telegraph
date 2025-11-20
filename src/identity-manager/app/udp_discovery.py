import socket, json, os

def run_server():
    udp_port = int(os.getenv("UDP_PORT", "5353"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", udp_port))   # escucha en todas las interfaces

    while True:
        data, addr = sock.recvfrom(1024)
        msg = json.loads(data.decode())

        if msg.get("action") == "discover":
            # responder al cliente con la IP del DNS
            response = {"status": "active"}
            sock.sendto(json.dumps(response).encode(), addr)