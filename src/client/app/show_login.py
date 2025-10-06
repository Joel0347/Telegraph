# archivo listo para ser borrado si todo funciona

import streamlit as st
from services.api_handler_service import ApiHandlerService
from services.client_info_service import ClientInfoService

def show_login():
    api_srv = ApiHandlerService()
    client_srv = ClientInfoService()
    
    columns = st.columns(5)
    with columns[2]:
        st.image("static/logo_no_bg.png", width=160)
    
    st.title("Telegraph - Inicio de Sesión")

    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")
    
    col1, col2 = st.columns([1, 3])
    login = False
    with col1:
        if st.button("Iniciar Sesión", type='primary'):
            login = True

    with col2:
        if st.button("Registrarse", type='primary'):
            st.session_state.page = "register"
            st.rerun()
            
    if login and api_srv.login_register(username, password, action="login"):
        client_srv.save_username(username)
        st.session_state.page = "chat"
        st.rerun()