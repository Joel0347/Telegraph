import streamlit as st
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService
from components.ui_module import UIModule
from typing import Literal


class AuthModule(UIModule):
    def __init__(self, api_service: ApiHandlerService, client_service: ClientInfoService):
        self.api_service = api_service
        self.client_service = client_service

    def show(self, action: Literal["login", "register"]):
        page_title = "Inicio de Sesión" if action == "login" else "Registro"
        columns = st.columns(5)
        with columns[2]:
            st.image("static/images/logo_no_bg.png", width=160)
        
        st.title(f"Telegraph - {page_title}")

        username = st.text_input("Usuario", key=f"{action}_user")
        password = st.text_input("Contraseña", type="password", key=f"{action}_pass")
        confirm_password = st.text_input("Confirmar Contraseña", type="password", key=f"reg_pass_confirm") \
            if action == "register" else None
        
        col1, col2 = st.columns([1, 3])
        btn_pressed = False
        btn_label = "Iniciar Sesión" if action == "login" else "Crear cuenta"
        with col1:
            if st.button(f"{btn_label}", type='primary'):
                btn_pressed = True

        with col2:
            if action == "login":
                if st.button("Registrarse", type='primary'):
                    st.session_state.page = "register"
                    st.rerun()
            else: 
                if st.button("Volver", type='primary'):
                    st.session_state.page = "login"
                    st.rerun()
        if btn_pressed:
            if action == "register" and password != confirm_password:
                st.error("Las contraseñas no coinciden")
                return
            if self.api_service.login_register(username, password, action=action):
                self.client_service.save_username(username)
                st.session_state.page = "chat"
                st.rerun()