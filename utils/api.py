# Path: frontend/utils/api.py
# API utility functions for making requests to the backend server.
import pandas as pd
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

FASTAPI_BASE_URL = os.getenv("HF_API_URL", "http://localhost:7860")

@st.cache_data(ttl=600)
def get_available_models() -> dict:
    """ Fetches available models via FastAPI """
    fallback_data = {
        "models": ["defog/llama-3-sqlcoder-8b:featherless-ai"],
        "default_model": "defog/llama-3-sqlcoder-8b:featherless-ai"
    }
    try:
       resp = requests.get(f"{FASTAPI_BASE_URL}/models", timeout=10)
       resp.raise_for_status()
       return resp.json()
    except Exception as e:
        st.warning(f"Backend unreachable. Using fallback models.")
        return fallback_data

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