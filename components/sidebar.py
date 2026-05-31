# Path: frontend/components/sidebar.py
# Sidebar component for navigation and additional options.
import streamlit as st
from utils.api import get_available_models
from components.auth import render_auth_dialog, save_chat_history, save_userDB, load_userDB

@st.dialog("Delete Confirmation")
def confirm_delete(idx, session_title):
    st.warning(f"Are you sure you want to delete '{session_title}'?")
    st.write(":material/warning: This action cannot be undone!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("Delete", type="primary", use_container_width=True):
            deleted_session = st.session_state.chat_sessions.pop(idx)
            st.toast("Item permanently deleted!", icon=":material/delete:")

            if st.session_state.messages == deleted_session.get("messages", []):
                st.session_state.messages = []

            db = load_userDB()
            if st.session_state.username in db:
                db[st.session_state.username]["sessions"] = st.session_state.chat_sessions
                save_userDB(db)
            st.rerun()

def render_sidebar():
    with st.sidebar:
        #st.subheader(":material/sql:", anchor=False)
        if st.session_state.auth_stat == 'guest':
            if st.button(":material/login: Login / Sign Up", type="secondary", use_container_width=True):
                render_auth_dialog()
        else:
            if st.button(":material/logout: Logout", use_container_width=True):
                st.session_state.auth_stat = 'guest'
                st.session_state.username = 'guest'
                st.session_state.messages = []
                if "chat_sessions" in st.session_state:
                    del st.session_state.chat_sessions
                st.rerun()

        if st.button(":material/add: New Chat", use_container_width=True):
            if st.session_state.auth_stat != 'guest':
                save_chat_history(st.session_state.username, st.session_state.messages)
            st.session_state.messages = []
            st.rerun()
        st.divider()

        st.caption("Database Connection")
        st.success(icon=":material/circle:", body="Connected")

        st.caption("Model Selector")
        available_models = get_available_models()
        st.session_state.current_model = st.selectbox(
            "Select model:",
            available_models,
            label_visibility="collapsed"
        )
        st.divider()

        st.caption("History")
        if st.session_state.auth_stat == 'guest':
            st.info("You are in Guest Mode. Your conversation history will not be saved.")
        else:
            st.caption(f"Authenticated as: {st.session_state.username}")
            if "chat_sessions" not in st.session_state:
                db = load_userDB()
                st.session_state.chat_sessions = db.get(st.session_state.username, {}).get("sessions", [])
 
            if st.session_state.messages:
                st.button(f":material/chat_bubble: Active Session Logs", disabled=True, use_container_width=True)

            if not st.session_state.chat_sessions:
                st.caption('Query your database now')
            else:
                for idx, session in enumerate(st.session_state.chat_sessions):
                    col1, col2 = st.columns([0.80, 0.20])

                    with col1:
                        session_title = session.get("title", f"Chat {idx + 1}")
                        if st.button(
                            f":material/history: {session_title[:15]}...",
                            key=f"load_session_{idx}",
                            use_container_width=True
                        ):
                            st.session_state.messages = session.get("messages", [])
                            st.rerun()

                    with col2:
                        if st.button(":material/delete:", key=f"delete_session_{idx}"):
                            confirm_delete(idx, session_title)