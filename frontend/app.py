# Path: frontend/app.py
# Main application file for the frontend, setting up the app and routing.
import streamlit as st
from components import auth, sidebar, chat

st.set_page_config(page_icon=":material/sql:", page_title="NL2SQL Assistant", layout="wide")

# Initialize global session state variables
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'guest_mode' not in st.session_state:
    st.session_state['guest_mode'] = False
if 'current_session_id' not in st.session_state:
    st.session_state['current_session_id'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

def main():
    if st.session_state['user_id'] is None and not st.session_state['guest_mode']:
        # User not logged in, show authentication page
        auth.render_auth()
    else:
        sidebar.render_sidebar()
        chat.render_chat_interface()

if __name__ == "__main__":
    main()