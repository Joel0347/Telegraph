import streamlit as st
import threading, os
from server import start_flask_server
from show_login import show_login
from show_register import show_register
from show_chat import show_chat
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService

if "page" in st.session_state and st.session_state.page == "chat":
    st.set_page_config(page_title="Telegraph", layout="wide")
else:
    st.set_page_config(page_title="Telegraph", layout="centered")

# Iniciar el servidor Flask en segundo plano (para recibir mensajes HTTP)
if "flask_started" not in st.session_state:
    threading.Thread(target=start_flask_server, daemon=True).start()
    st.session_state.flask_started = True

# Lógica de navegación
if "page" not in st.session_state:
    st.session_state.page = "login"
# if "username" not in st.session_state:
#     st.session_state.username = ""
client_srv = ClientInfoService()
if username := client_srv.get_username():
    api_srv = ApiHandlerService()
    api_srv.notify_online(username)
    # st.session_state.username = os.getenv('USERNAME')
    st.session_state.page = "chat"

if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "register":
    show_register()
elif st.session_state.page == "chat":
    show_chat()
