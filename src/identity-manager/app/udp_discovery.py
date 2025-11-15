import socket, json, os, fcntl, struct

def get_local_ip(ifname="eth0") -> str:
    # obtiene la IP overlay del contenedor
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

    return ip

# def get_overlay_network(ifname="eth0") -> ipaddress.IPv4Network:
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#     # IP local
#     ip = get_local_ip(s, ifname)

#     # Netmask
#     netmask = socket.inet_ntoa(fcntl.ioctl(
#         s.fileno(),
#         0x891b,  # SIOCGIFNETMASK
#         struct.pack('256s', ifname[:15].encode())
#     )[20:24])

#     # Construir red
#     net = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
#     return net

def run_server():
    dns_port = int(os.getenv("DNS_PORT", "5353"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", dns_port))   # escucha en todas las interfaces

    while True:
        data, addr = sock.recvfrom(1024)
        msg = json.loads(data.decode())

        if msg.get("action") == "discover":
            # responder al cliente con la IP del DNS
            response = {"status": "active"}
            sock.sendto(json.dumps(response).encode(), addr)