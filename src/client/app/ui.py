import streamlit as st
import requests
from messaging import send_message
from storage import load_messages  # Asegúrate de tener estas funciones
from storage import mark_messages_as_read
from messaging import get_chat
API_URL = "http://identity-manager:8000"

def show_login():
    st.title("Telegraph - Inicio de Sesion")

    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    if st.button("Iniciar Sesion"):
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            st.session_state.username = username
            st.session_state.page = "chat"
        else:
            _publish_status(res.json())

    if st.button("Registrarse"):
        st.session_state.page = "register"

def show_register():
    st.title("Telegraph - Registro")

    username = st.text_input("Nuevo usuario", key="reg_user")
    password = st.text_input("Nueva contraseña", type="password", key="reg_pass")

    if st.button("Crear cuenta"):
        res = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
        if res.status_code == 200:
            st.success("Registro exitoso. Ahora puedes iniciar sesión.")
            st.session_state.page = "login"
        else:
            _publish_status(res.json())

    if st.button("Volver al Inicio de Sesion"):
        st.session_state.page = "login"

def show_chat():
    username = st.session_state.username

    # Cargar mensajes del usuario actual
    user_chats = load_messages(username)

    # Sidebar: lista de chats
    st.sidebar.title("Chats")
    chat_partners = list(user_chats.keys())

    # Estado para el chat seleccionado
    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None

    # Sidebar: lista de chats
    selected = st.sidebar.radio("Conversaciones", chat_partners, index=chat_partners.index(st.session_state.selected_chat) if st.session_state.selected_chat in chat_partners else 0) if chat_partners else None
    if selected:
        st.session_state.selected_chat = selected

    # Área principal tipo Telegram
    if st.session_state.selected_chat:
        # Marcar como leídos los mensajes recibidos
        mark_messages_as_read(username, st.session_state.selected_chat)

        st.markdown(f"<h2 style='text-align:center;'>{st.session_state.selected_chat}</h2>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        # Mostrar historial con timestamp y estado leído
        chat_msgs = get_chat(username, st.session_state.selected_chat)
        chat_box = st.container()
        with chat_box:
            for msg in chat_msgs:
                ts = msg.get("timestamp", "")
                leido = "✅" if msg.get("leido") else "🕓"
                if msg["from"] == username:
                    st.markdown(f"<div style='text-align:right; color:green;'>Tú: {msg['text']}<br><span style='font-size:10px;'>{ts} {leido}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:left; color:blue;'>{msg['from']}: {msg['text']}<br><span style='font-size:10px;'>{ts} {leido}</span></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        if "msg_input_key" not in st.session_state:
            st.session_state.msg_input_key = 0
        with st.form(key="send_msg_form"):
            new_msg = st.text_input("Escribe tu mensaje", key=f"msg_input_{st.session_state.msg_input_key}")
            send_btn = st.form_submit_button("Enviar")
            if send_btn and new_msg.strip():
                result = send_message(username, st.session_state.selected_chat, new_msg)
                st.success(result)
                st.session_state.msg_input_key += 1
                st.rerun()
    else:
        st.info("No tienes chats activos. Escribe a alguien para comenzar.")

    with st.sidebar.expander("Nuevo chat"):
        # Obtener lista de usuarios desde el backend
        try:
            res = requests.get(f"{API_URL}/users")
            if res.status_code == 200:
                all_users = [u["username"] for u in res.json() if u["username"] != username]
            else:
                all_users = []
        except Exception:
            all_users = []
        if all_users:
            new_receiver = st.selectbox("Selecciona usuario para chatear", all_users, key="new_chat_select")
            if st.button("Iniciar chat", key="start_chat_btn"):
                st.session_state.selected_chat = new_receiver
                if new_receiver not in user_chats:
                    user_chats[new_receiver] = []
                st.rerun()
        else:
            st.info("No hay otros usuarios disponibles para chatear.")

def _publish_status(response: dict): 
    if response.get("status") == 200:
        st.success(response['message'])
    elif response.get("status") == 409:
        st.warning(response['message'])
    elif response.get("status") == 500:
        st.error(response['message'])
    else:
        st.error("Error inesperado")

def launch_ui():
    # Inicializa el estado de navegación
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "username" not in st.session_state:
        st.session_state.username = ""

    # Navegación
    if st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "register":
        show_register()
    elif st.session_state.page == "chat":
        show_chat()
