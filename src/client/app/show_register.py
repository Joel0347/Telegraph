import streamlit as st
import os
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService

def show_register():
    api_srv = ApiHandlerService()
    client_srv = ClientInfoService()
    
    st.title("Telegraph - Registro")

    username = st.text_input("Usuario", key="reg_user")
    password = st.text_input("Contraseña", type="password", key="reg_pass")
    confirm_password = st.text_input("Confirmar Contraseña", type="password", key="reg_pass_confirm")

    col1, col2 = st.columns([1, 3])
    register = False
    with col1:
        if st.button("Crear cuenta", type='primary'):
            register = True
                
    with col2:
        if st.button("Volver", type='primary'):
            st.session_state.page = "login"
            st.rerun()

    if register:
        if password != confirm_password:
            st.error("Las contraseñas no coinciden")
            return
        
        if api_srv.login_register(username, password, action="register"):
            client_srv.save_username(username)
            # st.session_state.username = username
            st.session_state.page = "chat"
            st.rerun()