import streamlit as st
from show_login import show_login
from show_register import show_register
from show_chat import show_chat


if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = ""

if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "register":
    show_register()
elif st.session_state.page == "chat":
    show_chat()