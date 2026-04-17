# Test the Hugging Face inference
from src.nl2sql.hf_engine import generate_sql
from src.database.db_manager import get_db_connection, get_schema_context
import pandas as pd

def test_single_query():
    print("Initializing Featherless AI SQL generation test...")
    # Fetch the database schema context (ddl) from Chinook
    ddl = get_schema_context
    question = "Identify the artist who has earned the most revenue from customers in Canada."

    try:
        generated_sql = generate_sql(question, ddl)
        print(f"\nGenerated SQL:\n{generated_sql}\n")

        # Connect to the database and execute the generated SQL
        connection = get_db_connection()
        df = pd.read_sql_query(generated_sql, connection)
        connection.close()

        print("\nDatabase Query Result:")
        print(df)
        print("\nTest completed successfully: API connected and SQL is valid.")

    except Exception as e:
        print(f"\nTest failed: {e}")

if __name__ == "__main__":
    test_single_query()