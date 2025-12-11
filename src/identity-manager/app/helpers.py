import socket, fcntl, struct, ipaddress, logging, threading
from bcrypt import checkpw, hashpw, gensalt

logging.basicConfig(level=logging.INFO)
lock = threading.Lock()
blocked = False

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
        
def hash_password(plaintext_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt and returns the hashed password as a UTF-8 string.

    Args:
        planetext_password (str): The plaintext password to hash.

    Returns:
        str: The bcrypt-hashed password.
    """
    return hashpw(plaintext_password.encode('utf-8'), gensalt()).decode('utf-8')

def check_password(plain_pwd: str, hashed_pwd: str) -> bool:
    """
    Checks whether a password is correct or not.

    Args:
        plain_pwd (str): The plain password inserted by user.
        hashed_pwd (str): The hashed password saved in database.

    Returns:
        bool: `True` if `plain_pwd` is the correct password, otherwise `False`
    """
    return checkpw(plain_pwd.encode('utf-8'), hashed_pwd.encode('utf-8'))