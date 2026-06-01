# Path: backend/server/api_server.py
# FatAPI entry point
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.src.database.db_manager import get_db_connection
from backend.src.nl2sql.hf_engine import get_models, DEFAULT_MODEL_ID
from backend.src.nl2sql.sql_agent import nl2sql_agent

load_dotenv()
app = FastAPI(title="NL2SQL Backend API")

class chatRequest(BaseModel):
    question: str
    model_id: Optional[str] = DEFAULT_MODEL_ID

class chatResponse(BaseModel):
    status: str
    sql: str
    answer: str
    data: List[Dict[str, Any]]
    error: str

@app.get("/models", response_model=List[str])
def api_get_models():
    """ Endpoint to fetch available models """
    try:
        models = get_models()
        return models if models else [DEFAULT_MODEL_ID]
    except Exception as e:
        return [DEFAULT_MODEL_ID, "Qwen/Qwen2.5-Coder-7B-Instruct:featherless-ai"]

@app.post("/chat", response_model=chatResponse)
def api_process_chat(request: chatRequest):
    """ Endpoint to process NL2SQL question and return data """
    try:
        resp = nl2sql_agent(user_question=request.question, model_id=request.model_id)

        sql_query = resp.get('query', 'N/A')
        nl_response = resp.get('nl_response', 'Could not synthesize text answer')
        status = resp.get('status', 'error')
        error_msg = resp.get('error', '')

        results_list = []
        execution_error = ""

        if status != 'error' and sql_query != 'N/A':
            conn = get_db_connection()
            if conn:
                try:
                    df = pd.read_sql_query(sql_query, conn)
                    results_list = df.to_dict(orient="records")
                except Exception as e:
                    execution_error = str(e)
                    status = "error"
                finally:
                    conn.close()
            else:
                execution_error = ":material/warning: Failed to connect to the database."
                status = "error"
        return chatResponse(
            status = status,
            sql = sql_query,
            answer = nl_response,
            data = results_list,
            error = execution_error if execution_error else error_msg
        )
    except Exception as e:
        return chatResponse(
            status = "error",
            sql = "N/A",
            answer = "An unexpected error occurred.",
            data = [],
            error = str(e)
        )