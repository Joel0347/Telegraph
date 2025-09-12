import streamlit as st
import requests

API_URL = "http://identity-manager:8000"

def launch_ui():
    st.title("Cliente WhatsApp P2P")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Registrar"):
        res = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
        st.success(res.json()['message'])

    if st.button("Login"):
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        st.success(res.json()['message'])
        st.write(res.json())

    receiver = st.text_input("Destinatario")
    message = st.text_input("Mensaje")

    if st.button("Enviar mensaje"):
        from messaging import send_message
        result = send_message(username, receiver, message)
        st.success(result)