# Path: src/nl2sql/sql_agent.py
# SQL Agent for handling NL2SQL conversion with Auto-Correct functionality
from backend.src.database.db_manager import get_db_connection, get_schema_context
from langchain_core.prompts import PromptTemplate
from backend.src.nl2sql.hf_engine import get_llm

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

REFINEMENT_PROMPT_TEMPLATE = """You are an expert SQLite developer.
You previously generated a SQL query to answer the user's question, but it resulted inan error when executed on the database.

Schema Context:
{schema}

User Question:
{question}

Previous Generated SQL:
{failed_sql}

Database Error Message:
{error_message}

Your task is to fix the SQL query based on the exact error message and the schema.
Pay close attention to column names, table relationships, and SQLite syntax.
Return ONLY the raw, corrected SQL query. 
Do not include any explanations, markdown formatting, or code blocks.

Corrected SQL Query:"""

# Generate text response
NL_RESPONSE_TEMPLATE = """You are a helpful data assisstant.
The user asked the following question: "{question}"
The database returned the following results: {results}

Provide a direct, natural language answer to the user's question using ONLY the provided data.
Keep it brief. Do not explain the SQL query or mention the database schema.
If the database returns more than 5 rows, DO NOT list the items individually. Instead, provide a brief summary sentence.

Answer:"""

prompt_template = PromptTemplate(
    input_variables = ["schema", "question"],
    template = SQL_PROMPT_TEMPLATE
)

refinement_prompt = PromptTemplate(
    input_variables = ["schema", "question", "failed_sql", "error_message"],
    template = REFINEMENT_PROMPT_TEMPLATE
)

nl_response_template = PromptTemplate(
    input_variables = ["question", "results"],
    template = NL_RESPONSE_TEMPLATE
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
def nl2sql_agent(user_question: str, max_retries: int = 3) -> dict:
    """
    Complete flow execution with Auto-correction:
    Get Schema context -> Generate SQL query -> Execute SQL query -> If Error, Refine & Retry ->Return results
    """
    # Fetch database schema context using RAG
    print(f"Fetching RAG schema context for: '{user_question}'...")
    schema = get_schema_context(question = user_question)

    # Generate SQL query using the schema context and user question
    llm = get_llm()

    # LangChain Pipeline: Pipe prompt into LLM
    chain = prompt_template | llm
    refinement_chain = refinement_prompt | llm
    nl_chain = nl_response_template | llm

    current_sql = ""
    error_message = ""

    # Auto-correction Loop
    for attempt in range(1, max_retries + 1):
        if attempt == 1:
            print("Generating initial SQL query...")
            raw_response = chain.invoke({
                "schema": schema,
                "question": user_question
            })
        else:
            print(f"\n--- Attempt {attempt}/{max_retries}: Refining SQL query based on error ---")
            print(f"Feeding error back to LLM: {error_message}")
            raw_response = refinement_chain.invoke({
                "schema": schema,
                "question": user_question,
                "failed_sql": current_sql,
                "error_message": error_message
            })

            # Parse & clean the generated SQL query
            generated_sql = clean_sql(raw_response)
            current_sql = generated_sql
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
                
                if attempt > 1:
                    print(f"SQL query executed successfully after {attempt} attempts.")
                
                # Generate natural language response based on the results
                print("Generating natural language response based on query results...")
                nl_response = nl_chain.invoke({
                    "question": user_question,
                    "results": str(results)
                })

                return {
                    "query": generated_sql,
                    "results": results,
                    "nl_response": nl_response,
                    "status": "success",
                    "attempts": attempt
                }
            except Exception as e:
                error_message = str(e)
                print(f"Error executing SQL: {error_message}")

                if attempt == max_retries:
                    print("Max retries reached. Returning error.")
            finally:
                connection.close()
    
    return {
        "query": current_sql,
        "error": error_message,
        "status": f"Error executing SQL after {max_retries} attempts"
    }