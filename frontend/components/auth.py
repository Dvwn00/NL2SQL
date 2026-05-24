# Path: frontend/components/auth.py
# Authentication component for handling user login and registration.
import streamlit as st
from utils import api

def render_auth():
    st.title("Welcome to NL2SQL Assistant Demo")
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                response = api.user_login(email, password)
                if response.get("success"):
                    st.session_state['user_id'] = response.get("user_id")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
    
    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                st.success("Account created successfully! Plase login to continue.")
    
    st.divider()
    st.markdown("Or continue as a guest:")
    if st.button("Continue as Guest", use_container_width=True):
        st.session_state['guest_mode'] = True
        st.rerun()