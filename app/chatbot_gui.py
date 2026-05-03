# Path: app/chatbot_gui.py
# Chatbot GUI for NL2SQL Application
import os
import streamlit as st
import pandas as pd
from src.nl2sql.sql_agent import nl2sql_agent
from src.database.db_manager import get_db_connection

# Page Configuration
st.set_page_config(
    page_title="NL2SQL Assistant", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS for styling
def load_css(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = os.path.join("assets", "style.css")
try:
    load_css(css_path)
except FileNotFoundError:
    st.warning(f"Warning: CSS file not found at {css_path}")

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Left Panel: Sidebar for database connection, model selector and user history
with st.sidebar:
    col_title, col_icon = st.columns([4, 1], vertical_alignment="center")
    with col_title:
        st.header("NL2SQL Assistant")
    with col_icon:
        if st.button("", icon=":material/edit_square:", help="New Chat"):
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    st.subheader("Database Connection")
    conn = get_db_connection()
    if conn:
        st.success(":material/database: Connected")
        conn.close()
    else:
        st.error(":material/database_off: Disconnected")

    st.divider()
    st.subheader("Model Selection")
    model_options = st.selectbox(
        "Choose a model:",
        ["defog/llama-3-sqlcoder-8b", "Qwen2.5-Coder-7B-Instruct"],
        label_visibility="collapsed"
    )
    st.caption(f"Selected model: {model_options.split('/')[0]}")

    st.divider()
    st.subheader(":material/history: History")
    history_container = st.container(height=200, border=False)

    with history_container:
        if not st.session_state.messages:
            st.caption("No History")
        else:
            for idx, msg in enumerate(st.session_state.messages):
                if msg["role"] == "user":
                    button_text = msg["content"][:28] + "..." if len(msg["content"]) > 28 else msg["content"]
                    st.button(button_text, key=f"history_{idx}", icon=":material/chat_bubble:", use_container_width=True)
    
    st.divider()
    profile_col, settings_col = st.columns([3, 1], vertical_alignment="center")
    with profile_col:
        st.button("", icon=":material/account_circle:", use_container_width=True, help="User Profile")
        st.toast("User profile feature coming soon!")
    with settings_col:
        if st.button("", icon=":material/settings:", help="Setting"):
            st.toast("Settings panel coming soon!")

# Right Panel: Main chat interface
st.title("NL2SQL Assistant: Chat with your database")

for msg in st.session_state.messages:
    avatar_icon = ":material/person:" if msg["role"] == "user" else ":material/smart_toy:"

    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("status") == "success":
            with st.expander("View Generated SQL Query"):
                st.code(msg["query"], language="sql")

            if msg.get("df") is not None:
                st.dataframe(msg["df"])

# User input and processing
if prompt := st.chat_input("Ask a question about your database..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        with st.spinner("Translating to SQL and querying database..."):
            response = nl2sql_agent(user_question=prompt)

            if response.get("status") == "success":
                nl_resp = response.get("nl_response")
                st.markdown(nl_resp)

                generated_sql = response.get("query")
                with st.expander("View Generated SQL Query"):
                    st.code(generated_sql, language="sql")

                results = response.get("results")
                if results:
                    df = pd.DataFrame(results)
                    st.dataframe(df)

                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Data as CSV",
                        data=csv,
                        file_name='query_results.csv',
                        mime='text/csv',
                        icon=":material/download:"
                    )
                else:
                    df = None
                    st.info("Query executed successfully but returned no results.")

                # Save successful response to History
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": nl_resp,
                    "status": "success",
                    "query": generated_sql,
                    "df": df
                })

                # Update the History list instantly
                st.rerun()
            else:
                # Handle error message
                error_msg = f"Error: {response.get('error', 'An unknown error occurred.')}"
                st.error(error_msg)

                with st.expander("View Failed SQL"):
                    st.code(response.get("query"), language="sql")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "status": "error"
                })
