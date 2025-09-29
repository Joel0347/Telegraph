import socket
import streamlit as st


global API_URL
API_URL = "http://identity-manager:8000"


def get_local_ip():
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _socket.connect(("8.8.8.8", 80))
        ip = _socket.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        _socket.close()
    return ip

def publish_status(response: dict): 
    if response.get("status") == 200:
        st.success(response['message'])
    elif response.get("status") != 500:
        st.warning(response['message'])
    else:
        st.error(response['message'])