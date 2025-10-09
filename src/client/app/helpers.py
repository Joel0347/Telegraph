import socket, os
import streamlit as st


def get_local_ip() -> str:
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _socket.connect(("8.8.8.8", 80))
        ip = _socket.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        _socket.close()
    return ip

def get_local_port() -> int:
    return int(os.getenv("API_PORT", 8000))

def publish_status(response: dict): 
    if response.get("status") == 200:
        return
    elif response.get("status") != 500:
        st.warning(response['message'])
    else:
        st.error(response['message'])

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

