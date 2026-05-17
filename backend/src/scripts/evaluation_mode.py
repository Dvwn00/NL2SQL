# Path: src/scripts/evaluation_mode.py
# Evaluation script for Hugging Face SQL generation.
import json
import sqlglot
from pathlib import Path
import pandas as pd
from src.database.db_manager import get_db_connection
from src.nl2sql.hf_engine import get_models
from src.nl2sql.sql_agent import nl2sql_agent
from src.scripts.taxonomy_report import print_taxonomyReport

TEST_CASES_PATH = Path("src/scripts/test_cases.json")

def _normalize_dataframe(dataframe: pd.DataFrame) -> list:
    # Normalize dataframe to ensure accurate comparison
    """
    Standardize dataframes for Execution Accuracy (EX).
    - Converts dataframe to a list of tuples to ignore column names.
    - Rounds floating points to 4 decimal places to avoid precision mismatch.
    - Sorts the final list to ensure order-agnostic comparison.
    """
    if dataframe is None or dataframe.empty:
        return []
    
    normalized = dataframe.copy()

    for column in normalized.columns:
        normalized[column] = normalized[column].map(
            lambda x: round(float(x), 4)
            if pd.api.types.is_numeric_dtype(type(x)) and isinstance(x, float)
            else x
            #lambda value: round(float(value), 6)
            #if isinstance(value, (float, int))
            #else value
        )

    # Convert to list of tuples for order-agnostic comparison
    data_tuples = [tuple(row) for row in normalized.to_numpy()]

    # Sort to ensure order agnoticism
    try:
        data_tuples.sort(key=lambda x: str(x))
    except Exception as e:
        pass
        
    return data_tuples

# Semantic safety net
def extract_tables(sql: str) -> set:
    """
    Extract a set of all table names used in a SQL query.
    Used to catch false positives where EX passes but the model queried the wrong tables.
    """
    if not sql:
        return set()
    try:
        parsed = sqlglot.parse_one(sql, read=None)

        # Find all table expressions & extract names, ignore aliases
        return set(table.name.lower() for table in parsed.find_all(sqlglot.exp.Table) if table.name)
    except Exception as e:
        return set()

# EX: Compare generated SQL results with expected results
def calculate_ex(df_generated: pd.DataFrame, df_gold: pd.DataFrame) -> bool:
    """
    Execution Accuracy (EX): Compare generated SQL results with expected results.
    """
    if df_generated is None or df_gold is None:
        return False

    #if normalized_generated.shape != normalized_gold.shape:
    #        return False
    
    try:
        normalized_generated = _normalize_dataframe(df_generated)
        normalized_gold = _normalize_dataframe(df_gold)
        
        return normalized_generated == normalized_gold

    except Exception as error:
        print(f"EX Evaluation Error: {error}")
        return False

def calculate_esm(generated_sql: str, gold_sql: str) -> bool:
    """
    Exact Set Match (ESM): Compare AST structure using sqlglot.
    - Ignores formatting, capitalization, and minor syntactic sugar.
    """
    if not generated_sql or not gold_sql:
        return False
    
    try:
        # Parse both SQL queries into expressions
        generated_exp = sqlglot.parse_one(generated_sql, read=None)
        gold_exp = sqlglot.parse_one(gold_sql, read=None)

        # Compare the expressions for structural equivalence
        return generated_exp == gold_exp
    except Exception as error:
        print(f"ESM Evaluation Error: {error}")
        return False

def run_evaluation(model_id: str):
    print(f"\nRunning SQL evaluation for model: {model_id}")
    print("\n" + "-" *50)

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
        print(f"Testing ID {id}: {question[:40]}...")

        # Implement agent to handle RAG retrieval and SQL generation
        agent_response = nl2sql_agent(user_question=question, model_id=model_id)
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

            # Trap the False Positive (empty set): weak test case
            if df_gold.empty:
                print(f"[!]WARNING: Gold SQL for ID {id} returned an emoty response.")

            ex_result = calculate_ex(df_generated, df_gold)

            # Semantic safety net check
            if ex_result:
                gen_tables = extract_tables(generated_sql)
                gold_tables = extract_tables(gold_sql)

                if gen_tables != gold_tables:
                    print(f"[X] FALSE POSITIVE (ID{id}): Data matched, tables not")
                    print(f"\nGenerated SQL tables: {gen_tables} | Gold SQL tables: {gold_tables}")
                    ex_result = False
        
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
    print(f"Model Evaluated: {model_id}")
    print(f"Total Test Cases: {total}")
    print(f"Execution Accuracy (EX): {ex_accuracy:.2f}% ({ex_count}/{total})")
    print(f"Exact Set Match (ESM): {esm_accuracy:.2f}% ({esm_count}/{total})")

    safe_model_name = model_id.replace("/", "_").replace(":", "_")
    output_file = Path(f"sql_eval_{safe_model_name}.json")
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=4)

    print_taxonomyReport(results)

if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())

    models_to_test = get_models()
    for model in models_to_test:
        run_evaluation(model)