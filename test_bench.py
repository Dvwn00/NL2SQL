# Test the database connection and schema extraction

import pandas as pd
from src.database.db_manager import get_db_connection, get_schema_context
from src.nl2sql.qwen_engine import query_qwen, build_qwen_prompt

def run_test(question):
    print(f"\n[USER QUESTION]: {question}")

    # Step 1: Get the database schema context from db_manager
    schema = get_schema_context()

    # Step 2: Build the prompt and Generate SQL query
    prompt = build_qwen_prompt(question, schema)
    generated_sql = query_qwen(prompt)
    print(f"\n[GENERATED SQL]:\n{generated_sql}")

    # Step 3: Execute the generated SQL query against the database
    try:
        connection = get_db_connection()
        # Use pandas to execute the SQL query and display results
        result_df = pd.read_sql_query(generated_sql, connection)
        connection.close()

        print("[EXECUTION SUCCESS]:")
        if result_df.empty:
            print("Query returned no results.")
        else:
            print(result_df.head(5))  # Display the first 5 rows of the result
    except Exception as e:
        print(f"[EXECUTION ERROR]: {e}")

if __name__ == "__main__":
    # Example test question
    test_question = "What is the total revenue generated from each country?"
    run_test(test_question)