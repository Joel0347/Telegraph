import streamlit as st
from streamlit_autorefresh import st_autorefresh
from sender import send_message
from repositories.msg_repo import MessageRepository
from services.msg_service import MessageService
from services.api_handler_service import ApiHandlerService

def show_chat():
    msg_repo = MessageRepository()
    api_srv = ApiHandlerService()
    msg_srv = MessageService(msg_repo, api_srv)
    username = st.session_state.username
    st_autorefresh(interval=2000, key="chat_autorefresh")
    api_srv.send_heart_beat(username)
    user_chats = msg_srv.load_conversations(username)

    if st.sidebar.button("Cerrar Sesión", type='primary'):
        api_srv.logout()
        st.session_state.page = "login"
        st.session_state.pop('username')
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
        msg_srv.mark_as_read(username, st.session_state.selected_chat)
        _render_chat_area(username)
    else:
        st.info("No tienes chats activos. Escribe a alguien para comenzar.")

    _create_new_chat(username)
    
def _render_chat_area(username):
    msg_repo = MessageRepository()
    api_srv = ApiHandlerService()
    msg_srv = MessageService(msg_repo, api_srv)
    st.markdown(f"<h2 style='text-align:center;'>{st.session_state.selected_chat}</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    chat_msgs = msg_srv.get_chat(username, st.session_state.selected_chat)
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

def _create_new_chat(username):
    api_srv = ApiHandlerService()
    
    with st.sidebar.expander("Nuevo chat"):
        all_users = api_srv.get_users(username)
        
        if all_users:
            new_receiver = st.selectbox("Selecciona usuario para chatear", all_users, key="new_chat_select")
            
            if st.button("Iniciar chat", key="start_chat_btn"):
                st.session_state.selected_chat = new_receiver
                st.rerun()
        else:
            st.info("No hay otros usuarios disponibles para chatear.")
