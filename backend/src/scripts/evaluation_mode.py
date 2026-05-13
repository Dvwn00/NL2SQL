# Path: src/scripts/evaluation_mode.py
# Evaluation script for Hugging Face SQL generation.
import json
import sqlglot
from pathlib import Path
import pandas as pd
from src.database.db_manager import get_db_connection
from src.nl2sql.sql_agent import nl2sql_agent
from src.scripts.taxonomy_report import print_taxonomyReport

TEST_CASES_PATH = Path("src/scripts/test_cases.json")
RESULTS_PATH = Path("hf_evaluation_results.json")

def _normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    # Normalize dataframe to ensure accurate comparison
    """
    Standardize dataframes for Execution Accuracy (EX).
    - Ensures Order Agnoticism by sorting all values.
    - Prepares for Column Agnoticism by focuing on value comparison rather than column names.
    """
    normalized = dataframe.copy()
    #normalized.columns = [str(column).lower() for column in normalized.columns]

    for column in normalized.columns:
        normalized[column] = normalized[column].map(
            lambda value: round(float(value), 6)
            if isinstance(value, (float, int))
            else value
        )

    sort_columns = list(normalized.columns)
    if sort_columns:
        normalized = normalized.sort_values(by=sort_columns).reset_index(drop=True)

    return normalized

# EX: Compare generated SQL results with expected results
def calculate_ex(df_generated: pd.DataFrame, df_gold: pd.DataFrame) -> bool:
    """
    Execution Accuracy (EX): Compare generated SQL results with expected results.
    - Column Name Agnostic: Use .values to ignore header differences.
    """
    if df_generated is None or df_gold is None:
        return False

    try:
        normalized_generated = _normalize_dataframe(df_generated)
        normalized_gold = _normalize_dataframe(df_gold)

        if normalized_generated.shape != normalized_gold.shape:
            return False
        
        return bool((normalized_generated.values == normalized_gold.values).all())
        # return normalized_generated.equals(normalized_gold)
    except Exception as error:
        print(f"EX Evaluation Error: {error}")
        return False

def calculate_esm(generated_sql: str, gold_sql: str) -> bool:
    """
    Exact Set Match (ESM): Compare AST structure using sqlglot.
    - Ignores formatting, capitalization, and minor syntactic sugar.
    """
    try:
        # Parse both SQL queries into expressions
        generated_exp = sqlglot.parse_one(generated_sql, read=None)
        gold_exp = sqlglot.parse_one(gold_sql, read=None)

        # Compare the expressions for structural equivalence
        return generated_exp == gold_exp
    except Exception as error:
        print(f"ESM Evaluation Error: {error}")
        return False

def run_evaluation():
    if not TEST_CASES_PATH.exists():
        print(f"Error: Could not find test cases at {TEST_CASES_PATH}")
        return
    
    with TEST_CASES_PATH.open("r", encoding="utf-8") as handle:
        test_cases = json.load(handle)

    results = []
    ex_count = 0
    esm_count = 0

    print(f"Running evaluation on {len(test_cases)} test cases...\n")

    for case in test_cases:
        id = case.get("id")
        question = case.get("question")
        gold_sql = case.get("gold_sql")
        taxonomy = case.get("taxonomy", "Unknown")
        # print(f"Testing ID {id}: {question[:50]}...")

        # Implement agent to handle RAG retrieval and SQL generation
        agent_response = nl2sql_agent(user_question=question)
        generated_sql = agent_response.get("query", "")

        # ESM Evaluation
        esm_result = calculate_esm(generated_sql, gold_sql)
        if esm_result:
            esm_count += 1

        # EX Evaluation
        ex_result = False
        connection = get_db_connection()
        if connection is None:
            raise RuntimeError("Unable to connect to the SQLite database.")

        try:
            df_generated = pd.read_sql_query(generated_sql, connection)
            df_gold = pd.read_sql_query(gold_sql, connection)

            ex_result = calculate_ex(df_generated, df_gold)
            if ex_result:
                ex_count += 1
        except Exception as error:
            print(f"Error executing SQL for ID {id}: {error}")
        finally:
            connection.close()

        results.append({
            "id": id,
            "question": question,
            "taxonomy": taxonomy,
            "ex_pass": ex_result,
            "esm_pass": esm_result,
            "generated_sql": generated_sql,
            "gold_sql": gold_sql
        })
    
    # Summary Statistics
    total = len(test_cases)
    ex_accuracy = (ex_count / total) * 100 if total > 0 else 0
    esm_accuracy = (esm_count / total) * 100 if total > 0 else 0

    print("\nEVALUATION SUMMARY")
    print("-" * 40)
    print(f"Total Test Cases: {total}")
    print(f"Execution Accuracy (EX): {ex_accuracy:.2f}% ({ex_count}/{total})")
    print(f"Exact Set Match (ESM): {esm_accuracy:.2f}% ({esm_count}/{total})")

    with RESULTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=4)

    print_taxonomyReport(results)