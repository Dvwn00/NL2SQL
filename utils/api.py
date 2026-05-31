# Path: frontend/utils/api.py
# API utility functions for making requests to the backend server.
import pandas as pd
import streamlit as st
import requests
from typing import List, Dict, Any, Tuple

FASTAPI_BASE_URL = "http://localhost:8000"

@st.cache_data(ttl=600)
def get_available_models() -> List[str]:
    """ Fetches available models via FastAPI """
    try:
       resp = requests.get(f"{FASTAPI_BASE_URL}/models", timeout=10)
       resp.raise_for_status()
       return resp.json()
    except Exception as e:
        st.warning(f"Backend unreachable. Using fallback models. Error: {e}")
        return ["Qwen/Qwen2.5-Coder-7B-Instruct:featherless-ai"]

def process_userPrompt(question: str, model_id: str) -> Dict[str, Any]:
    """ Send user's question to FastAPI and parses the response """
    try:
        payload = {
            "question": question,
            "model_id": model_id
        }

        resp = requests.post(f"{FASTAPI_BASE_URL}/chat", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        df_results = pd.DataFrame(data["data"]) if data.get("data") else pd.DataFrame()

        return {
            "status": data["status"],
            "sql": data["sql"],
            "answer": data["answer"],
            "data": df_results,
            "error":  data["error"]
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "sql": "N/A",
            "answer": "Failed to connect to the backend server.",
            "data": pd.DataFrame(),
            "error": str(e)
        }