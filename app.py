# Path: frontend/app.py
# Main application entry point, setting up the app and routing.
import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent
backend_dir = project_root / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# if str(current_dir) not in sys.path:
#     sys.path.insert(0, str(current_dir))

import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat_interface

st.set_page_config(
    page_icon=":material/sql:",
    page_title="NL2SQL Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# def load_css():
#     """Load custom CSS file"""
#     css_path = os.path.join("assets", "styles.css")
#     if os.path.exists(css_path):
#         with open(css_path) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_session_state():
    """Initialize global variables and authentication states"""
    if 'auth_stat' not in st.session_state:
        st.session_state.auth_stat = "guest"

    if 'username' not in st.session_state:
        st.session_state.username = "guest"

    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    if 'current_model' not in st.session_state:
        st.session_state.current_model = "default"

def main():
    # load_css()
    init_session_state()

    render_sidebar()
    render_chat_interface()

if __name__ == "__main__":
    main()