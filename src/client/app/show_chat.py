import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh
from sender import send_message
from repositories.msg_repo import MessageRepository
from services.msg_service import MessageService
from shared import API_URL, publish_status

def show_chat():
    repo = MessageRepository()
    service = MessageService(repo)
    username = st.session_state.username
    st_autorefresh(interval=2000, key="chat_autorefresh")
    user_chats = service.load_conversations(username)

    if st.sidebar.button("Cerrar Sesión", type='primary'):
        res = requests.post(f"{API_URL}/logout", json={"username": username})
        publish_status(res.json())
        st.session_state.page = "login"
        st.rerun()

    st.sidebar.title("Chats")
    chat_partners = list(user_chats.keys())

    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None

    index = chat_partners.index(st.session_state.selected_chat) \
        if st.session_state.selected_chat in chat_partners else 0
        
    selected = st.sidebar.radio(
        "Conversaciones", chat_partners, 
        index=index
    ) if chat_partners else None
    
    if selected:
        st.session_state.selected_chat = selected

    if st.session_state.selected_chat:
        service.mark_as_read(username, st.session_state.selected_chat)
        user_chats = service.load_conversations(username)
        _render_chat_area(username)
    else:
        st.info("No tienes chats activos. Escribe a alguien para comenzar.")

    _create_new_chat(username, user_chats)
    
def _render_chat_area(username):
    repo = MessageRepository()
    service = MessageService(repo)
    st.markdown(f"<h2 style='text-align:center;'>{st.session_state.selected_chat}</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    chat_msgs = service.get_chat(username, st.session_state.selected_chat)
    # CSS para el área scrolleable
    st.markdown(
        """
        <style>
        .chat-scroll-box {
            height: 350px;
            overflow-y: auto;
            background: #0e1117;
            border-radius: 12px;
            border: 1px solid #222;
            padding: 14px 8px 8px 8px;
            margin-bottom: 0.5rem;
        }
        .msg-right { text-align: right; }
        .msg-bubble-right {
            display: inline-block;
            background: #2e7d32;
            color: white;
            padding: 10px 14px;
            border-radius: 10px;
            margin: 2px 0;
            max-width: 70%;
            font-size: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .msg-left { text-align: left; }
        .msg-bubble-left {
            display: inline-block;
            background: #424242;
            color: white;
            padding: 10px 14px;
            border-radius: 10px;
            margin: 2px 0;
            max-width: 70%;
            font-size: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .msg-meta {
            font-size: 10px;
            color: #cfcfcf;
            margin-top: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # Construir HTML de todos los mensajes en un solo string
    chat_html = "<div class='chat-scroll-box'>"
    for msg in chat_msgs:
        ts = msg.get("timestamp", "")
        if msg["from"] == username:
            read = "✅" if msg.get("read") else "🕓"
            chat_html += (
                f"<div class='msg-right'>"
                f"<div class='msg-bubble-right'>"
                f"{msg['text']}<br>"
                f"<span class='msg-meta'>{ts} {read}</span>"
                f"</div>"
                f"</div>"
            )
        else:
            chat_html += (
                f"<div class='msg-left'>"
                f"<div class='msg-bubble-left'>"
                f"{msg['text']}<br>"
                f"<span class='msg-meta'>{ts}</span>"
                f"</div>"
                f"</div>"
            )
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
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

def _create_new_chat(username, user_chats):
    repo = MessageRepository()
    service = MessageService(repo)
    
    with st.sidebar.expander("Nuevo chat"):
        try:
            res = requests.get(f"{API_URL}/users")
            if res.json()["status"] == 200:
                all_users = [u["username"] for u in res.json()['usernames'] if u["username"] != username]
            else:
                all_users = []
        except Exception:
            all_users = []
        
        if all_users:
            new_receiver = st.selectbox("Selecciona usuario para chatear", all_users, key="new_chat_select")
            
            if st.button("Iniciar chat", key="start_chat_btn"):
                # if new_receiver not in user_chats:
                #     service.save_message(username, new_receiver, "")
                
                st.session_state.selected_chat = new_receiver
                st.rerun()
        else:
            st.info("No hay otros usuarios disponibles para chatear.")
