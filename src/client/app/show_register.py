import streamlit as st
import requests, os
from shared import get_local_ip, publish_status, API_URL

def show_register():
    st.title("Telegraph - Registro")

    username = st.text_input("Usuario", key="reg_user")
    password = st.text_input("Contraseña", type="password", key="reg_pass")
    confirm_password = st.text_input("Confirmar Contraseña", type="password", key="reg_pass_confirm")

    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("Crear cuenta", type='primary'):
            if password != confirm_password:
                st.error("Las contraseñas no coinciden")
                return
            
            ip = get_local_ip()
            os.environ['USERNAME'] = username

            res = requests.post(f"{API_URL}/register", json={
                "username": username,
                "password": password,
                "ip": ip,
                "port": int(os.getenv("API_PORT", 8000)),
                "status": "online"
            })

            publish_status(res.json())

            if res.json()["status"] == 200:
                st.session_state.username = username
                st.session_state.page = "chat"
                st.rerun()
                
    with col2:
        if st.button("Volver", type='primary'):
            st.session_state.page = "login"
            st.rerun()
