# Path: frontend/components/chat.py
# Chat component for handling user interactions and displaying chat history.
import streamlit as st
import pandas as pd
from utils.api import process_userPrompt
from components.auth import save_chat_history

def render_chat_interface():
    st.title(":material/sql: NL2SQL Assistant")
    st.divider()

    if not st.session_state.messages:
        for _ in range(5):
            st.write("")
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.subheader(":material/calendar_view_month: Ask a question about your data (e.g., 'Which country has the highest revenue? Give country name and amount.')", anchor=False)

    for idx, message in enumerate(st.session_state.messages):
        role = message.get("role", "assistant")
        content = message.get("content", "")

        with st.chat_message(role):
            st.markdown(content)

            if message.get("dataframe") is not None:
                raw_data = message["dataframe"]

                if isinstance(raw_data, list):
                    display_df = pd.DataFrame(raw_data)
                else:
                    display_df = raw_data
                
                st.dataframe(display_df, use_container_width=True)
                # display_df = message["dataframe"]
                # st.dataframe(message["dataframe"], use_container_width=True)

                csv_data = display_df.to_csv().encode('utf-8')
                if st.download_button(
                    label=":material/download: Download CSV",
                    data=csv_data,
                    file_name=f'query_results_{idx}.csv',
                    mime='text/csv',
                    key=f"download_{idx}"
                ):
                    st.toast("The file has been downloaded!")
    
    if prompt := st.chat_input("Ask a question about yout data..."):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Analyzing schema metadata and generating execution context..."):
                payload = process_userPrompt(
                    question=st.session_state.messages[-1]["content"],
                    model_id=st.session_state.current_model
                )

            if payload["status"] == "error":
                st.error(f"Interrupted:\n{payload['error']}")
                response_text = f"Failed to compute response due to error: {payload['error']}"
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.markdown(payload["answer"])
                st.code(payload["sql"], language="sql")
                
                display_df = payload["data"]
                if not display_df.empty:
                    display_df = display_df.copy()
                    display_df.index = range(1, len(display_df) + 1)
                    display_df.index.name = "No."
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"{payload['answer']}\n\n```sql\n{payload['sql']}\n```",
                    "dataframe": display_df if not display_df.empty else None
                })

                if st.session_state.auth_stat != 'guest':
                    save_chat_history(st.session_state.username, st.session_state.messages)

                st.rerun()