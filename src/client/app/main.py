import streamlit as st
import threading, os
from server import start_flask_server
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService
from components.auth import AuthModule
from components.chat import ChatModule
from PIL import Image

# Cargar logo para favicon
logo_path = "static/images/logo_no_bg.ico"
logo_img = None
try:
    logo_img = Image.open(os.path.join(os.path.dirname(__file__), logo_path))
except Exception:
    logo_img = None

if "page" in st.session_state and st.session_state.page == "chat":
    st.set_page_config(page_title="Telegraph", layout="wide", page_icon=logo_img or "📝")
else:
    st.set_page_config(page_title="Telegraph", layout="centered", page_icon=logo_img or "📝")

# Iniciar el servidor Flask en segundo plano (para recibir mensajes HTTP)
if "flask_started" not in st.session_state:
    threading.Thread(target=start_flask_server, daemon=True).start()
    st.session_state.flask_started = True

# Lógica de navegación
if "page" not in st.session_state:
    st.session_state.page = "login"

client_srv = ClientInfoService()
api_srv = ApiHandlerService()
auth_module = AuthModule(api_srv, client_srv)
chat_module = ChatModule(api_srv, client_srv)

if username := client_srv.get_username():
    if not api_srv.check_is_active(username):
        client_srv.remove_username()
        st.rerun()
  
    api_srv.notify_online(username)
    st.session_state.page = "chat"

if st.session_state.page == "login":
    auth_module.show(action="login")
elif st.session_state.page == "register":
    auth_module.show(action="register")
elif st.session_state.page == "chat":
    chat_module.show()
