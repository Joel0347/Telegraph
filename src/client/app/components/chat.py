import streamlit as st
from streamlit_autorefresh import st_autorefresh
from components.ui_module import UIModule
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService
from services.msg_service import MessageService
from repositories.msg_repo import MessageRepository
from helpers import render_html_template, inject_css


class ChatModule(UIModule):
    def __init__(self, api_service: ApiHandlerService, client_service: ClientInfoService):
        self.api_srv = api_service
        self.client_srv = client_service
        self._msg_repo = MessageRepository()
        self.msg_srv = MessageService(self._msg_repo, api_service)

    def show(self):
        username = self.client_srv.get_username()
        
        st_autorefresh(interval=4000, key="chat_autorefresh")
        user_chats = self.msg_srv.load_conversations(username)
        self.api_srv.send_heart_beat(username)
        online_users = self.api_srv.get_online_users(username)

        if st.sidebar.button("Cerrar Sesión", type='primary'):
            self.api_srv.logout(username)
            st.session_state.page = "login"
            self.client_srv.remove_username()
            st.rerun()

        st.sidebar.title("Chats")
        chat_partners = [g.name for g in user_chats]

        # Obtener usuarios online
        online_set = set(online_users) if online_users else set()

        # Construir lista de info para la sidebar
        sidebar_items = []
        for partner in chat_partners:
            group = next((g for g in user_chats if g.name == partner), None)
            msgs = group.messages if group else []

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
            inject_css("sidebar_chats.css")
            html_preview = render_html_template(
                "sidebar_chats.html",
                selected="yes" if is_selected else "no",
                btn_label=item["name"]
            )

            st.sidebar.markdown(html_preview, unsafe_allow_html=True)
            if st.sidebar.button("Abrir chat", key=f"chat_{item['name']}", use_container_width=True):
                st.session_state.selected_chat = item["name"]
                st.rerun()

            inject_css("sidebar_contacts.css")
            html_preview = render_html_template(
                "sidebar_contacts.html",
                status_class="online" if item["online"] else "offline",
                last_msg=item["last_msg"]
            )

            st.sidebar.markdown(html_preview, unsafe_allow_html=True)

        if st.session_state.selected_chat:
            self.msg_srv.mark_as_read(username, st.session_state.selected_chat)
            self._render_chat_area(username)
        else:
            st.info("""
                No tienes chats activos. Escribe a alguien para comenzar o selecciona
                'Nuevo chat' en la barra lateral.
            """)

        self._create_new_chat(username)

    def _render_chat_area(self, username):
        inject_css("chat_header.css")
        html_preview = render_html_template("chat_header.html", chat_with=st.session_state.selected_chat)
        st.markdown(html_preview, unsafe_allow_html=True)
        chat_msgs = self.msg_srv.get_chat(username, st.session_state.selected_chat)
        chat_box = st.container()

        with chat_box:
            for msg in chat_msgs:
                if msg.from_ == username:
                    inject_css("sent_msg.css")
                    html_preview = render_html_template(
                        "sent_msg.html",
                        read="✓" if msg.read else "◴",
                        msg=msg.text,
                        status="read" if msg.read else "unread",
                        ts=str(msg.timestamp)
                    )

                    st.markdown(html_preview, unsafe_allow_html=True)

                else:
                    inject_css("received_msg.css")
                    html_preview = render_html_template(
                        "received_msg.html",
                        msg=msg.text,
                        ts=str(msg.timestamp)
                    )

                    st.markdown(html_preview, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        if "msg_input_key" not in st.session_state:
            st.session_state.msg_input_key = 0

        new_msg = st.chat_input(
            "Escribe tu mensaje", 
            key=f"msg_input_{st.session_state.msg_input_key}"
        )

        if new_msg:
            self.msg_srv.send_message(username, st.session_state.selected_chat, new_msg)
            st.session_state.msg_input_key += 1
            st.rerun()

    def _create_new_chat(self, username):
        with st.sidebar.expander("Nuevo chat"):
            all_users = self.api_srv.get_users(username)
            
            if all_users:
                new_receiver = st.selectbox("Selecciona usuario para chatear", all_users, key="new_chat_select")
                
                if st.button("Iniciar chat", key="start_chat_btn"):
                    st.session_state.selected_chat = new_receiver
                    st.rerun()
            else:
                st.info("No hay otros usuarios disponibles para chatear.")