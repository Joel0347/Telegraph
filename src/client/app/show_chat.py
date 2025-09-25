import streamlit as st
import os
import json
import requests
from streamlit_autorefresh import st_autorefresh
from storage import get_storage_path
from messaging import send_message
from storage import load_messages
from storage import mark_messages_as_read
from messaging import get_chat
from shared import API_URL

def show_chat():
    username = st.session_state.username
    st_autorefresh(interval=2000, key="chat_autorefresh")
    user_chats = load_messages(username)

    if st.sidebar.button("Cerrar Sesión", type='primary'):
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
        mark_messages_as_read(username, st.session_state.selected_chat)
        user_chats = load_messages(username)
        _render_chat_area(username)
    else:
        st.info("No tienes chats activos. Escribe a alguien para comenzar.")

    _create_new_chat(username, user_chats)
    
def _render_chat_area(username):
    st.markdown(f"<h2 style='text-align:center;'>{st.session_state.selected_chat}</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    chat_msgs = get_chat(username, st.session_state.selected_chat)
    chat_box = st.container()
    with chat_box:
        for msg in chat_msgs:
            ts = msg.get("timestamp", "")
            leido = "✅" if msg.get("leido") else "🕓"
            if msg["from"] == username:
                st.markdown(f"""
                    <div style='text-align:right;'>
                        <div style='display:inline-block; background-color:#2e7d32; color:white; padding:10px; border-radius:10px; max-width:70%; box-shadow:0px 2px 5px rgba(0,0,0,0.2);'>
                            {msg['text']}<br>
                            <span style='font-size:10px; color:#cfcfcf;'>{ts} {leido}</span>
                        </div>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='text-align:left;'>
                        <div style='display:inline-block; background-color:#424242; color:white; padding:10px; border-radius:10px; max-width:70%; box-shadow:0px 2px 5px rgba(0,0,0,0.2);'>
                            {msg['text']}<br>
                            <span style='font-size:10px; color:#cfcfcf;'>{ts} {leido}</span>
                        </div>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
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
                if new_receiver not in user_chats:
                    storage_path = get_storage_path(username)
                    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
                    
                    if not os.path.exists(storage_path):
                        chats = {}
                    else:
                        with open(storage_path, "r") as f:
                            try:
                                chats = json.load(f)
                            except json.JSONDecodeError:
                                chats = {}
                    chats[new_receiver] = []
                    with open(storage_path, "w") as f:
                        json.dump(chats, f, indent=2)
                
                st.session_state.selected_chat = new_receiver
                st.rerun()
        else:
            st.info("No hay otros usuarios disponibles para chatear.")
