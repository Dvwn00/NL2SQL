# Path: src/nl2sql/sql_agent.py
# SQL Agent for handling NL2SQL conversion
from src.database.db_manager import get_db_connection, get_schema_context
from langchain_core.prompts import PromptTemplate
from src.nl2sql.hf_engine import get_llm

# Craft the Prompt Template to instruct LLM on its persona
SQL_PROMPT_TEMPLATE = """You are an expert SQLite developer.
Your task is to write a syntactically correct SQLite query to answer the user's question based strictly on the provided database schema.
Return ONLY the raw SQL query.
Do not include any explanations, markdown formatting, or code blocks.

Schema Context:
{schema}

User Question:
{question}

SQL Query:"""

prompt_template = PromptTemplate(
    input_variables = ["schema", "question"],
    template = SQL_PROMPT_TEMPLATE
)

# Clean the output
def clean_sql(raw_sql: str) -> str:
    """
    Utility to strip markdown formatting if the LLM hallucinated code blocks.
    Ensure the raw string can be directly executed by the SQLite cursor.
    """
    cleaned = raw_sql.strip()
    if cleaned.startswith("```sql"):
        cleaned = cleaned[6:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()

# Function to handle NL2SQL conversion
def nl2sql_agent(user_question: str) -> dict:
    """
    Complete flow execution:
    Get Schema context -> Generate SQL query -> Execute SQL query -> Return results
    """
    # Fetch database schema context using RAG
    print(f"Fetching RAG schema context for: '{user_question}'...")
    schema = get_schema_context(question = user_question)

    # Generate SQL query using the schema context and user question
    print("Generating SQL query via LLM...")
    llm = get_llm()

    # LangChain Pipeline: Pipe prompt into LLM
    chain = prompt_template | llm
    raw_response = chain.invoke({
        "schema": schema,
        "question": user_question
    })

    # Parse & clean the generated SQL query
    generated_sql = clean_sql(raw_response)
    print(f"Generated SQL: \n{generated_sql}")

    # Execute the generated SQL query and fetch results
    connection = get_db_connection()
    if not connection:
        return {
            "query": generated_sql,
            "error": "Could not establish database connection",
            "status": "failed"
        }
    
    try:
        cursor = connection.cursor()
        cursor.execute(generated_sql)
        results = cursor.fetchall()
        return {
            "query": generated_sql,
            "results": results,
            "status": "success"
        }
    except Exception as e:
        return {
            "query": generated_sql,
            "error": str(e),
            "status": f"error executing SQL: {e}"
        }
    finally:
        connection.close()