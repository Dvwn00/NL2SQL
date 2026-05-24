# Path: frontend/components/sidebar.py
# Sidebar component for navigation and additional options.
import streamlit as st
from utils import api

def render_sidebar():
    with st.sidebar:
        if st.button(":material/add: New Chat", use_container_width=True):
            st.session_state['current_session_id'] = None
            st.session_state['messages'] = []
            st.rerun()
        st.divider()

        # Guest View
        if st.session_state['guest_mode']:
            st.info("You are in Guest Mode. Your conversation history will not be saved.")
            st.write("Create an account to save your queries.")
            if st.button("Log In / Sign Up", use_container_width=True):
                st.session_state['guest_mode'] = False
                st.rerun()
        # Authenticated User View
        else:
            st.header(":material/history: History")
            # Fetch history
            history = api.get_user_history(st.session_state['user_id'])

            for time_label, sessions in history.items():
                if sessions:
                    st.caption(time_label)
                    for session in sessions:
                        col1, col2 = st.columns([5, 1])

                        with col1:
                            if st.button(f":material/chat_bubble: {session['title'][:20]}", key=f"sel_{session['id']}", use_container_width=True):
                                st.session_state['current_session_id'] = session['id']
                                st.session_state['messages'] = api.get_session_messages(session['id'])
                                st.rerun()
                        with col2:
                            if st.button(":material/delete:", key=f"del_{session['id']}", help="Delete Chat History"):
                                if api.del_conversation(session['id']):
                                    if st.session_state['current_session_id'] == session['id']:
                                        st.session_state['current_session_id'] = None
                                        st.session_state['messages'] = []
                                    st.rerun()
            st.divider()
            if st.button(":material/logout: Logout", use_container_width=True):
                st.session_state['user_id'] = None
                st.session_state['messages'] = []
                st.rerun()