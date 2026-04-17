#"""Hugging Face inference helpers for SQL generation."""

import os
import re

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


load_dotenv()
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("Token Not Found!")

client = InferenceClient(api_key=hf_token)
MODEL_ID = "defog/llama-3-sqlcoder-8b:featherless-ai"


def _build_messages(question: str, schema_context: str):
    system_content = (
        "You are an expert SQLite assistant that converts natural language into one "
        "executable SQLite query.\n"
        "Rules:\n"
        "1. Use only tables, columns, and join paths present in the provided schema.\n"
        "2. Generate valid SQLite syntax only.\n"
        "3. Prefer exact column names from the schema, never invent columns.\n"
        "4. Use explicit JOIN conditions when multiple tables are required.\n"
        "5. Use GROUP BY for aggregates by entity, HAVING for aggregate filters, "
        "ORDER BY for ranking, and LIMIT for top-N requests.\n"
        "6. Return SQL only. No markdown, explanations, comments, or chain-of-thought.\n"
        "7. If a join is needed, use short aliases that remain readable.\n"
        "8. Produce a single SELECT statement."
    )

    user_content = f"""Database schema:
{schema_context}

Question:
{question}

Write the SQLite query that answers the question. Return only the SQL query."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _extract_sql(raw_response: str) -> str:
    text = raw_response.strip()
    fenced_match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    statement_match = re.search(
        r"(?is)\b(WITH|SELECT)\b.*?(;|$)",
        text,
    )
    if statement_match:
        text = statement_match.group(0).strip()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith(("--", "#"))
    ]
    sql = " ".join(lines).strip()
    if sql and not sql.endswith(";"):
        sql = f"{sql};"
    return sql


def generate_sql(question, ddl):
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=_build_messages(question, ddl),
            max_tokens=220,
            temperature=0,
        )
        raw_response = completion.choices[0].message.content or ""
        sql = _extract_sql(raw_response)
        return sql or raw_response.strip()
    except Exception as error:
        return f"Error: {error}"


if __name__ == "__main__":
    my_ddl = "CREATE TABLE tracks (id INTEGER PRIMARY KEY, title TEXT, genre TEXT);"
    my_question = "How many tracks are there in each genre?"

    print("Generating SQL query via Featherless AI...")
    try:
        result = generate_sql(my_question, my_ddl)
        print("-" * 20)
        print(result)
    except Exception as error:
        print(f"An error occurred: {error}")
