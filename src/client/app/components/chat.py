import streamlit as st
import json, os
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
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
            st.session_state.msg_draft = ""
            st.session_state.bg_tasks.shutdown(wait=False)
            del st.session_state.bg_tasks
            self.client_srv.remove_username()
            st.rerun()

        st.sidebar.title("Chats")
        chat_partners = [g.name for g in user_chats]
        online_set = set(online_users) if online_users else set()
        sidebar_items = []

        for partner in chat_partners:
            group = next((g for g in user_chats if g.name == partner), None)
            msgs = group.messages if group else []

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

        selected_idx = 0
        if st.session_state.selected_chat:
            for i, item in enumerate(sidebar_items):
                if item["name"] == st.session_state.selected_chat:
                    selected_idx = i
                    break

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
        html_preview = render_html_template(
            "chat_header.html", chat_with=st.session_state.selected_chat
        )
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
        if "msg_draft" not in st.session_state:
            st.session_state.msg_draft = ""
        if "show_emoji_picker" not in st.session_state:
            st.session_state.show_emoji_picker = False

        inject_css("emoji_picker.css")

        if "msg" not in st.session_state:
            st.session_state.msg = st.session_state.msg_draft

        cols = st.columns([0.06, 0.80])

        with cols[0]:
            st.button(
                "☺", key=f"emoji_toggle",
                on_click=self._toggle_emoji_picker
            )
        with cols[1]:
            subcols = st.columns([0.9, 0.1])
            with subcols[0]:
                st.text_input(
                    "", key="msg", placeholder="Escribe tu mensaje",
                    label_visibility="collapsed",
                    on_change=self._update_draft
                )

            with subcols[1]:
                if st.button("➤", key="msg_btn"):
                    draft = st.session_state.get("msg_draft", "").strip()
                    if draft:
                        self._send(username, draft)

        components.html(
            render_html_template(
                "keypress_event.html",
                placeholder="Escribe tu mensaje",
                btn_text="➤"
            ), height=0
        )

        self._render_emojis()

    def _create_new_chat(self, username):
        with st.sidebar.expander("Nuevo chat"):
            all_users = self.api_srv.get_users(username)
            
            if all_users:
                new_receiver = st.selectbox(
                    "Selecciona usuario para chatear", all_users, key="new_chat_select"
                )
                
                if st.button("Iniciar chat", key="start_chat_btn"):
                    st.session_state.selected_chat = new_receiver
                    st.rerun()
            else:
                st.info("No hay otros usuarios disponibles para chatear.")
    
    def _send(self, username: str, text: str):
        self.msg_srv.send_message(username, st.session_state.selected_chat, text)
        st.session_state.msg_draft = ""
        if "msg" in st.session_state:
            del st.session_state.msg
        st.session_state.msg_input_key += 1
        st.rerun()
    
    def _update_draft(self):
        st.session_state.msg_draft = st.session_state.get("msg", "")

    def _append_emoji(self, emoji: str):
        st.session_state.msg_draft = st.session_state.get("msg_draft", "") + emoji
        st.session_state.msg = st.session_state.msg_draft

    def _toggle_emoji_picker(self):
        st.session_state.show_emoji_picker = not st.session_state.get("show_emoji_picker", False)

    def _load_emojis(self):
        path = os.path.join(os.path.dirname(__file__), "..", "static", "emojis", "emojis.json")
        path = os.path.normpath(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(e) for e in data]
        except Exception:
            pass

        return ["😀","😃","😄","😁","🤣","😊","😍","😜","🤩","😎"]
    
    def _render_emojis(self):
        if st.session_state.show_emoji_picker:
            emojis = self._load_emojis()
            per_row = 10
            for i in range(0, len(emojis), per_row):
                row = emojis[i:i+per_row]
                cols_row = st.columns(len(row))
                for j, e in enumerate(row):
                    cols_row[j].button(
                        e, key=f"emoji_{i+j}",
                        on_click=self._append_emoji, args=(e,),
                        type="tertiary"
                    )