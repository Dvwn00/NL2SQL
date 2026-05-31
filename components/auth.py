# Path: frontend/components/auth.py
# Authentication component for handling user login and registration.
import hashlib
import json
import os
import streamlit as st
import pandas as pd
from typing import Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AUTH_DB_PATH = Path("backend/src/database/auth_db.json")

# Hashing password
def hash_password(password):
    """ Securely hashes a password """
    return hashlib.sha256(password.encode()).hexdigest()

# Load user JSON-databases
def load_userDB():
    """ Load authenticated credentials from local JSON file """
    if not AUTH_DB_PATH.exists():
        AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        admin_user = os.getenv("DEFAULT_ADMIN_PASS")
        if not admin_user:
            raise ValueError("SECURITY HALT: DEFAULT_ADMIN_PASS environment is missing. Cannot initialize database securely.")
        
        default_db = {
            "admin": {
                "password": hash_password(admin_user),
                "history": []
            }
        }

        with open(AUTH_DB_PATH, "w") as f:
            json.dump(default_db, f, indent=4)
        return default_db
    
    with open(AUTH_DB_PATH, "r") as f:
        return json.load(f)

# Sace user data into the JSON-databases    
def save_userDB(db_data: dict):
    with open(AUTH_DB_PATH, "w") as f:
        json.dump(db_data, f, indent=4)

# User registration/create new account
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """ Registers a new user record safely into the system """
    if not username or not password:
        return False, "Fields cannot be empty."
    
    db = load_userDB()
    if username in db:
        return False, "Username already exists. Please choose a different one."
    
    db[username] = {
        "password": hash_password(password),
        "history": []
    }
    save_userDB(db)
    return True, "Account registered successfully!"

# User login
def verify_login(username: str, password: str) -> bool:
    """ Verifies credentials against the authentication store """
    db = load_userDB()
    if username not in db:
        return False
    return db[username]["password"] == hash_password(password)

# Save user's conversation
def save_chat_history(username: str, session_messages: list):
    """ Saves user's conversation logs to history """
    if not username or username == "guest" or not session_messages:
        return
    
    db = load_userDB()
    if username in db:
        if "sessions" not in db[username]:
            db[username]["sessions"] = []

        # Sanitize messages to make df JSON-serializable
        sanitized_msg = []
        for msg in session_messages:
            clean_msg = {}
            for key, value in msg.items():
                if isinstance(value, pd.DataFrame):
                    clean_msg[key] = value.to_dict(orient="records")
                else:
                    clean_msg[key] = value
            sanitized_msg.append(clean_msg)

        first_prompt = next((m["content"] for m in session_messages if m["role"] == "user"), "New Query")
        truncated_title = first_prompt[:25]

        # Check whether update an existing session / append new history
        existing_sessions = db[username]["sessions"]
        session_exists = False

        for ses in existing_sessions:
            if ses.get("title") == truncated_title:
                ses["messages"] = sanitized_msg
                session_exists = True
                break
        
        if not session_exists:
            existing_sessions.append({
                "title": truncated_title,
                "messages": sanitized_msg
            })

        db[username]["sessions"] = existing_sessions
        save_userDB(db)
        st.session_state.chat_sessions = existing_sessions

# Retrieves user's history
def get_history(username: str) -> list:
    """ Retrieves saved conversation history for verified users """
    db = load_userDB()
    if username in db:
        return db[username].get("sessions", [])
    return []

@st.dialog("Account Access Panel")
def render_auth_dialog():
    """
    Streamlit UI native dialog: Handle custom login & signup cleanly without template injection
    """
    st.subheader("Sign In or Register")
    tab1, tab2 = st.tabs([":material/lock: Login", ":material/new: Create Account"])

    with tab1:
        login_user = st.text_input("Username", key="login_user_input")
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        if st.button("Authenticate", type="primary", use_container_width=True):
            if verify_login(login_user, login_pass):
                st.session_state.auth_stat = "logged_in"
                st.session_state.username = login_user
                st.session_state.messages = get_history(login_user)
                st.success(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid username or password credentials.")

    with tab2:
        reg_user = st.text_input("Username", key="reg_user_input")
        reg_pass = st.text_input("Password", type="password", key="reg_user_pass")
        reg_pass_confirm = st.text_input("Re-enter Password", type="password", key="reg_user_pass_confirm") 
        if st.button("Sign Up Now", use_container_width=True):
            if reg_pass != reg_pass_confirm:
                st.error("Password does not match!")
            else:
                success, msg = register_user(reg_user, reg_pass)
                if success:
                    st.success(msg)
                    # Login user automatically
                    st.session_state.auth_stat = "logged_in"
                    st.session_state.username = reg_user
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error(msg)