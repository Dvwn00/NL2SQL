# Evaluation Script for NL2SQL Models

import json
import pandas as pd
from src.database.db_manager import get_db_connection, get_schema_context
from src.nl2sql.qwen_engine import query_qwen, build_qwen_prompt

def compare_results(df_generated_sql, df_gold_sql):
    """Compares the generated SQL query with the expected SQL query."""
    if df_generated_sql is None or df_gold_sql is None:
        return False
    try:
        return df_generated_sql.values.tolist() == df_gold_sql.values.tolist()
    except Exception as e:
        print(f"Error comparing results: {e}")
        return False
    
def run_evaluation():
    # Load test cases from a JSON file
    with open('src/scripts/test_cases.json', 'r') as f:
        test_cases = json.load(f)

    results = []
    correct_count = 0
    schema = get_schema_context()

    print(f"Running evaluation on {len(test_cases)} test cases...\n")

    for case in test_cases:
        print(f"Testing ID {case['id']}: {case['question'][:50]}...")
        
        # Generate SQL query using the LLM
        prompt = build_qwen_prompt(case['question'], schema)
        generated_sql = query_qwen(prompt)

        # Execute both generated SQL and gold SQL
        connection = get_db_connection()
        try:
            df_generated = pd.read_sql_query(generated_sql, connection)
            df_gold = pd.read_sql_query(case['gold_sql'], connection)

            # Compare results
            is_correct = compare_results(df_generated, df_gold)
            if is_correct:
                correct_count += 1
            
            results.append({
                "id": case['id'],
                "status": "PASS" if is_correct else "FAIL",
                "generated": generated_sql
            })
        except Exception as e:
            results.append({"id": case['id'], "status": f"ERROR: {str(e)}"})
        finally:
            connection.close()
    
    # Print summary
    accuracy = (correct_count / len(test_cases)) * 100
    print(f"\n EVALUATION COMPLETE")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"Correctly Generated SQL: {correct_count}")
    print(f"Execution Accuracy: {accuracy:.2f}%")

    # Save results to a JSON file
    with open('evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    run_evaluation()