import streamlit as st
from streamlit.components.v1 import html
from streamlit_autorefresh import st_autorefresh
from sender import send_message
from repositories.msg_repo import MessageRepository
from services.msg_service import MessageService
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService

def show_chat():
    msg_repo = MessageRepository()
    api_srv = ApiHandlerService()
    msg_srv = MessageService(msg_repo, api_srv)
    client_srv = ClientInfoService()
    username = client_srv.get_username()
    
    st_autorefresh(interval=2000, key="chat_autorefresh")
    api_srv.send_heart_beat(username)
    user_chats = msg_srv.load_conversations(username)

    online_users = get_online_users(api_srv, username)
    if online_users:
        pending_mssgs_by_user = find_pending_mssgs_by_user(msg_srv, username, online_users)
        send_pending_mssgs(pending_mssgs_by_user, username)
    
    if st.sidebar.button("Cerrar Sesión", type='primary'):
        api_srv.logout(username)
        st.session_state.page = "login"
        client_srv.remove_username()
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
    
def get_online_users(api_srv, username):
    active_users = []
    try:
        all_users = api_srv.get_users(username)
        for u in all_users:
            user_info = api_srv.get_user_by_username(u)
            if user_info and user_info.get("status") == "online":
                active_users.append(u)
                
        return active_users
    except Exception as e:
        pass
    
def find_pending_mssgs_by_user(msg_srv, username, active_users):
    # --- NUEVO: Buscar mensajes pendientes por usuario activo ---
    pending_to_send = {}
    for other in active_users:
        chat_msgs = msg_srv.get_chat(username, other)
        # Solo revisar si hay mensajes en el chat
        if not chat_msgs:
            continue
        # Buscar el último mensaje enviado por el usuario actual
        last_idx = None
        for i in range(len(chat_msgs)-1, -1, -1):
            m = chat_msgs[i]
            if m["from"] == username:
                last_idx = i
                break
        if last_idx is None:
            continue
        # Si el último mensaje enviado está pendiente
        if chat_msgs[last_idx]["status"] == "pending":
            # Buscar hacia atrás todos los mensajes pendientes consecutivos
            first_pending_idx = last_idx
            for i in range(last_idx, -1, -1):
                m = chat_msgs[i]
                if m["from"] == username and m["status"] == "pending":
                    first_pending_idx = i
                elif m["from"] == username:
                    break
            # Guardar los mensajes pendientes a enviar
            pending_to_send[other] = chat_msgs[first_pending_idx:last_idx+1]
            
    return pending_to_send

def send_pending_mssgs(pending_to_send, username):
    # --- NUEVO: Enviar mensajes pendientes uno a uno ---
    for other, msgs in pending_to_send.items():
        for m in msgs:
            # Reenviar solo si sigue pendiente
            if m["status"] == "pending":
                send_message(username, other, m["text"])
   
def _render_chat_area(username):
    msg_repo = MessageRepository()
    api_srv = ApiHandlerService()
    msg_srv = MessageService(msg_repo, api_srv)
    # st.markdown(f"<h2 style='text-align:center;'>{st.session_state.selected_chat}</h2>", unsafe_allow_html=True)
    # st.markdown("<hr>", unsafe_allow_html=True)
    chat_msgs = msg_srv.get_chat(username, st.session_state.selected_chat)
    # CSS para el área scrolleable
    chat_box = st.container()
    with chat_box:
        for msg in chat_msgs:
                ts = msg.get("timestamp", "")
                if msg["from"] == username:
                    read = "✓" if msg.get("read") else "◴"
                    color = "#00CFFF" if msg.get("read") else "#cfcfcf"
                    st.markdown(f"""
                        <div style='text-align:right;'>
                            <div style='display:inline-block; background-color:#2e7d32; color:white;
                                        padding:10px; border-radius:10px; max-width:70%;
                                        box-shadow:0px 2px 5px rgba(0,0,0,0.2);
                                        text-align:left;'>
                                {msg['text']}<br>
                                <span style='font-size:10px; color:#cfcfcf; display:block; text-align:right;'>
                                    {ts} <span style="color:{color}; font-size:14px;">{read}</span>
                                </span>
                            </div>
                        </div>
                        <br>
                    """, unsafe_allow_html=True)

                else:
                    st.markdown(f"""
                        <div style='text-align:left;'>
                            <div style='display:inline-block; background-color:#424242; color:white; padding:10px; border-radius:10px; max-width:70%; box-shadow:0px 2px 5px rgba(0,0,0,0.2);'>
                                {msg['text']}<br>
                                <span style='font-size:10px; color:#cfcfcf; display:block; text-align:right;'>{ts}</span>
                            </div>
                        </div>
                        <br>
                    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if "msg_input_key" not in st.session_state:
        st.session_state.msg_input_key = 0
    # with st.form(key="send_msg_form"):
    new_msg = st.chat_input(
        "Escribe tu mensaje", 
        key=f"msg_input_{st.session_state.msg_input_key}"
    )
    # send_btn = st.form_submit_button("Enviar")
    if new_msg:
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
