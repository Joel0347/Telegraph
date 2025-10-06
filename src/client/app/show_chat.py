# archivo listo para ser borrado si todo funciona

import streamlit as st
from streamlit_autorefresh import st_autorefresh
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

    # Obtener usuarios online
    online_set = set(online_users) if online_users else set()

    # Construir lista de info para la sidebar
    sidebar_items = []
    for partner in chat_partners:
        msgs = user_chats[partner]
        # Si los mensajes son objetos Message, acceder con .text
        if msgs:
            last = msgs[-1]
            last_msg = getattr(last, "text", str(last))
        else:
            last_msg = ""
        is_online = partner in online_set
        sidebar_items.append({
            "name": partner,
            "online": is_online,
            "last_msg": last_msg
        })

    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None
    if st.session_state.selected_chat is None and sidebar_items:
        st.session_state.selected_chat = sidebar_items[0]["name"]
    # Mostrar lista custom y manejar selección
    selected_idx = 0
    if st.session_state.selected_chat:
        for i, item in enumerate(sidebar_items):
            if item["name"] == st.session_state.selected_chat:
                selected_idx = i
                break

    # Render manual de la lista y selección
    for i, item in enumerate(sidebar_items):
        is_selected = (i == selected_idx)
        btn_label = item["name"]
        btn_color = "#e7fbe9" if is_selected else "#fff"
        btn_style = f"background-color:{btn_color}; color:#222; border-radius:8px; border:none; width:100%; text-align:left; padding:8px 6px; margin-bottom:0px; font-weight:bold;"
        # Botón solo con el nombre, con estilo visual mejorado
        st.sidebar.markdown(f"""
            <div style='{btn_style}'>
                <span>{btn_label}</span>
            </div>
        """, unsafe_allow_html=True)
        if st.sidebar.button("Abrir chat", key=f"chat_{item['name']}", use_container_width=True):
            st.session_state.selected_chat = item["name"]
            st.rerun()
        # Mostrar preview y estado debajo
        color = "#25D366" if item["online"] else "#cfcfcf"
        st.sidebar.markdown(f"""
            <div style='display:flex; flex-direction:row; align-items:center; margin-bottom:10px; margin-top:-8px;'>
                <div style='width:10px; height:10px; border-radius:50%; background:{color}; margin-right:10px; margin-top:4px;'></div>
                <div style='flex:1;'>
                    <div style='font-size:12px; color:#666; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:140px;'>{item['last_msg']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.selected_chat:
        msg_srv.mark_as_read(username, st.session_state.selected_chat)
        _render_chat_area(username)
    else:
        st.info("No tienes chats activos. Escribe a alguien para comenzar o selecciona 'Nuevo chat' en la barra lateral.")

    _create_new_chat(username)
    
# NUEVO
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
    repo = MessageRepository()
    service = MessageService(repo)
    # --- NUEVO: Enviar mensajes pendientes uno a uno ---
    for other, msgs in pending_to_send.items():
        for m in msgs:
            # Reenviar solo si sigue pendiente
            if m["status"] == "pending":
                service.send_message(username, other, m["text"])
   
def _render_chat_area(username):
    msg_repo = MessageRepository()
    api_srv = ApiHandlerService()
    msg_srv = MessageService(msg_repo, api_srv)
    # Mostrar el nombre del usuario con quien se conversa
    chat_with = st.session_state.selected_chat
    st.markdown(f"<h2 style='text-align:center; margin-bottom: 0.5em;'>{chat_with}</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    chat_msgs = msg_srv.get_chat(username, chat_with)
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
        result = msg_srv.send_message(username, st.session_state.selected_chat, new_msg)
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
