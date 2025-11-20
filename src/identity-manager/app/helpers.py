import socket, fcntl, struct, ipaddress, logging

logging.basicConfig(level=logging.INFO)

def get_local_ip(s: socket.socket = None, ifname="eth0") -> str:
    # obtiene la IP overlay del contenedor
    if not s:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

    return ip

def get_overlay_network(ifname="eth0") -> ipaddress.IPv4Network:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # IP local
    ip = get_local_ip(s, ifname)

    # Netmask
    netmask = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x891b,  # SIOCGIFNETMASK
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

    # Construir red
    net = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
    return net

def publish_status(response: dict): 
    if response.get("status") == 200:
        return
    elif response.get("status") != 500:
        logging.info(response['message'])
    else:
        logging.info(response['message'])