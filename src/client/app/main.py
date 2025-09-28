import streamlit as st
import threading
from server import start_flask_server
from show_login import show_login
from show_register import show_register
from show_chat import show_chat

st.set_page_config(page_title="Telegraph", layout="centered")

# Iniciar el servidor Flask en segundo plano (para recibir mensajes HTTP)
if "flask_started" not in st.session_state:
    threading.Thread(target=start_flask_server, daemon=True).start()
    st.session_state.flask_started = True

# Lógica de navegación
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = ""

if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "register":
    show_register()
elif st.session_state.page == "chat":
    show_chat()
