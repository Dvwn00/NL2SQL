# Path: frontend/components/chat.py
# Chat component for handling user interactions and displaying chat history.
import streamlit as st
import pandas as pd
from utils import api

def render_chat_interface():
    st.title(":material/sql: NL2SQL Assistant")
    st.divider()
    
    # Render existing messages
    for msg in st.session_state['messages']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sql" in msg and msg["sql"]:
                st.code(msg["sql"], language="sql")
            if "data" in msg and msg["data"]:
                st.dataframe(pd.DataFrame(msg["data"]))
    
    # Input area for new messages
    if prompt := st.chat_input("Ask a question about your database (e.g., 'Show me top revenue in 2020')"):
        # Display user prompt
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process and get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Executing LangChain pipeline for RAG-based schema retrieval..."):
                response = api.send_chat_message(
                    user_id = st.session_state['user_id'],
                    session_id = st.session_state.get('current_session_id'),
                    message = prompt
                )

                # Render results
                st.markdown(response.get("answer", "Generated SQL based on the query:"))
                st.code(response["sql"], language="sql")
                if response.get("data"):
                    st.dataframe(pd.DataFrame(response["data"]))

                # Save conversations to session state
                st.session_state['messages'].append({
                    "role": "assistant",
                    "content": response.get("answer", ""),
                    "sql": response["sql"],
                    "data": response.get("data")
                })

                # Save session ID automatically if user is authenticated and it's a new session
                if not st.session_state['guest_mode'] and st.session_state['current_session_id'] is None:
                    st.session_state['current_session_id'] = response.get("session_id")