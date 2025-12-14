import socket, os, fcntl, struct, ipaddress
import streamlit as st
from time import sleep


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

def get_local_port() -> int:
    return int(os.getenv("API_PORT", 8000))

def publish_status(response: dict): 
    if response.get("status") == 200:
        return
    elif response.get("status") != 500:
        st.warning(response['message'])
    else:
        st.error(response['message'])

    sleep(2)
    st.rerun()

def render_html_template(file_name: str, **kwargs) -> str:
    path = f"./static/html/{file_name}"
    try:
        with open(path, "r", encoding="utf-8") as file:
            html = file.read()
        return html.format(**kwargs)
    except FileNotFoundError:
        return f"<div style='color:red;'>Archivo no encontrado: {path}</div>"
    except KeyError as e:
        return f"<div style='color:red;'>Falta variable: {e}</div>"
    except Exception as e:
        return f"<div style='color:red;'>Error al procesar HTML: {e}</div>"

def inject_css(file_name: str):
    path = f"./static/css/{file_name}"
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
