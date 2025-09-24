import streamlit as st
import requests
from shared import get_local_ip, publish_status, API_URL

def show_login():
    st.title("Telegraph - Inicio de Sesión")

    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")
    
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Iniciar Sesión", type='primary'):
            ip = get_local_ip()
            port = 9000
            res = requests.post(f"{API_URL}/login", json={
                "username": username,
                "password": password,
                "ip": ip,
                "port": port
            })
            publish_status(res.json())
            
            if res.json()["status"] == 200:
                st.session_state.username = username
                st.session_state.page = "chat"
                st.rerun()

    with col2:
        if st.button("Registrarse", type='primary'):
            st.session_state.page = "register"
            st.rerun()