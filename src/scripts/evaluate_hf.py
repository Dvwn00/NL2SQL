#"""Evaluation script for Hugging Face SQL generation."""

import json
from pathlib import Path

import pandas as pd

from src.database.db_manager import get_db_connection, get_schema_context
from src.nl2sql.hf_engine import generate_sql


TEST_CASES_PATH = Path("src/scripts/test_cases.json")
RESULTS_PATH = Path("hf_evaluation_results.json")


def _normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    normalized.columns = [str(column).lower() for column in normalized.columns]

    for column in normalized.columns:
        normalized[column] = normalized[column].map(
            lambda value: round(float(value), 6)
            if isinstance(value, float)
            else value
        )

    sort_columns = list(normalized.columns)
    if sort_columns:
        normalized = normalized.sort_values(by=sort_columns, kind="mergesort").reset_index(drop=True)

    return normalized


def compare_results(df_generated: pd.DataFrame, df_gold: pd.DataFrame) -> bool:
    """Compare generated and expected query results."""
    if df_generated is None or df_gold is None:
        return False

    try:
        normalized_generated = _normalize_dataframe(df_generated)
        normalized_gold = _normalize_dataframe(df_gold)
        return normalized_generated.equals(normalized_gold)
    except Exception as error:
        print(f"Error comparing results: {error}")
        return False


def run_evaluation():
    with TEST_CASES_PATH.open("r", encoding="utf-8") as handle:
        test_cases = json.load(handle)

    results = []
    correct_count = 0

    print(f"Running evaluation on {len(test_cases)} test cases...\n")

    for case in test_cases:
        question = case["question"]
        print(f"Testing ID {case['id']}: {question[:50]}...")

        schema_context = get_schema_context(question=question)
        generated_sql = generate_sql(question, schema_context)

        connection = get_db_connection()
        if connection is None:
            raise RuntimeError("Unable to connect to the SQLite database.")

        try:
            df_generated = pd.read_sql_query(generated_sql, connection)
            df_gold = pd.read_sql_query(case["gold_sql"], connection)

            is_correct = compare_results(df_generated, df_gold)
            if is_correct:
                correct_count += 1

            results.append(
                {
                    "id": case["id"],
                    "question": question,
                    "status": "PASS" if is_correct else "FAIL",
                    "generated_sql": generated_sql,
                    "gold_sql": case["gold_sql"],
                }
            )
        except Exception as error:
            results.append(
                {
                    "id": case["id"],
                    "question": question,
                    "status": "ERROR",
                    "generated_sql": generated_sql,
                    "gold_sql": case["gold_sql"],
                    "error": str(error),
                }
            )
        finally:
            connection.close()

    accuracy = (correct_count / len(test_cases)) * 100 if test_cases else 0.0
    print("\nEVALUATION COMPLETE")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"Correctly Generated SQL: {correct_count} / {len(test_cases)}")
    print(f"Execution Accuracy: {accuracy:.2f}%")

    with RESULTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=4)


if __name__ == "__main__":
    run_evaluation()
