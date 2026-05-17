# Path: src/scripts/interactive_mode.py
# Interactive mode: Allows user to manually type questions and see the agent's response
import csv
import json
import pandas as pd
from pathlib import Path
from tabulate import tabulate
from src.database.db_manager import get_db_connection
from src.nl2sql.sql_agent import nl2sql_agent
from src.nl2sql.hf_engine import get_models

TEST_CASES_PATH = Path("src/scripts/test_cases.json")

def get_query_data(sql_query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the results as a DataFrame.
    """
    if not sql_query or sql_query == "N/A":
        return pd.DataFrame()
    
    connection = get_db_connection()
    if not connection:
        return pd.DataFrame()

    try:
        df = pd.read_sql_query(sql_query, connection)
        return df
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()
    finally:
        connection.close()

def verify_data(df_gold: pd.DataFrame, df_generated: pd.DataFrame) -> bool:
    """
    Guardrail check:
    Verifies if the generated DataFrame matches the expected gold DataFrame.
    """
    if df_gold.empty and df_generated.empty:
        return False  # Both empty: To catch this as a potential issue
    
    if len(df_gold) != len(df_generated):
        return False
    
    try:
        gold_val = df_gold.fillna("").astype(str).values.tolist()
        gen_val = df_generated.fillna("").astype(str).values.tolist()

        # Strip whitespace and convert to tuples (sortable)
        gold_tuples = [tuple(val.strip() for val in row) for row in gold_val]
        gen_tuples = [tuple(val.strip() for val in row) for row in gen_val]

        return sorted(gold_tuples) == sorted(gen_tuples)
    except Exception as e:
        print(f"Error during data verification: {e}")
        return False


def run_interactiveMode(model_id: str):
    """ 
    Automates the interactive Question Answering mode.
    Runs predefined questions through the agent and logs the textual NL response.
    """
    print("\n========= Interactive NL2SQL Mode =========")
    print(f"Running Interactive Question Answering Evaluation on Model: {model_id}")
    #print("Type 'exit' or 'q' to return to the main menu.\n")

    if not TEST_CASES_PATH.exists():
        print(f"Error: Could not find test cases at {TEST_CASES_PATH}")
        return
    
    with TEST_CASES_PATH.open("r", encoding="utf-8") as handle:
        test_cases = json.load(handle)

    questAns_results = []

    for case in test_cases:
        case_id = case.get("id")
        question = case.get("question")
        gold_sql = case.get("gold_sql")
        print(f"\n\nTesting ID {case_id}: {question[:40]}...")

        response = nl2sql_agent(user_question=question, model_id=model_id)

        # Extract metadata
        status = response.get('status')
        nl_answer = response.get('nl_response', 'N/A')
        sql_query = response.get('query', 'N/A')
        error_msg = response.get('error', '')
        attempts = response.get('attempts', 0)

        # Data cross-check
        df_gold = get_query_data(gold_sql)
        df_generated = get_query_data(sql_query)

        # Verify accuracy
        is_data_accurate = verify_data(df_gold, df_generated)

        questAns_results.append({
            "id": case_id,
            "model_id": model_id,
            "question": question,
            "status": status,
            "data_returned_correct": is_data_accurate,
            "attempts": attempts,
            "nl_response": nl_answer,
            "sql_generated": sql_query,
            "error": error_msg
        })

    # Save to CSV for human-readable and easy comparison
    safe_model_name = model_id.replace("/", "_").replace(":", "_").replace(" ", "_")
    output_csv = Path(f"Q&A_report_{safe_model_name}.csv")

    keys = questAns_results[0].keys()
    with output_csv.open("w", newline='', encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(questAns_results)

    print(f"\nInteractive evaluation completed. Results saved to: {output_csv}")

if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

    models_to_test = get_models()
    for model in models_to_test:
        run_interactiveMode(model)