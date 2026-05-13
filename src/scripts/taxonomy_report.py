# Path: src/scripts/taxonomy_report.py
# Generate a taxonomy report to identify which taxonomy tags model struggles with
import json
import pandas as pd
from pathlib import Path

def print_taxonomyReport(results_data):
    """
    Generates and prints taxonomy breakdown.
    Accepts either a list of dictionaries (from memory) or reads from the default JSON
    """
    if not results_data:
        results_path = Path("hf_evaluation_results.json")
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                results_data = json.load(f)
        else:
            print("No data provided and results file not found.")
            return
        
    if not results_data:
        return
    
    df = pd.DataFrame(results_data)
    df['taxonomy'] = df['taxonomy'].fillna("Unknown").astype(str)
    df['taxonomy'] = df['taxonomy'].str.split(', ')
    df_exploded = df.explode('taxonomy')

    # Calculate Accuract per Taxonomy Tag
    taxonomy_summary = df_exploded.groupby('taxonomy').agg(
        total_cases = ('id', 'count'),
        ex_passed = ('ex_pass', 'sum'),
        esm_passed = ('esm_pass', 'sum')
    )

    taxonomy_summary['ex_acc'] = (taxonomy_summary['ex_passed'] / taxonomy_summary['total_cases']) * 100
    taxonomy_summary['esm_acc'] = (taxonomy_summary['esm_passed'] / taxonomy_summary['total_cases']) * 100

    print("\n" + "="*50)
    print("TAXONOMY PERFORMANCE REPORT SUMMARY")
    print("-"*50)

    # Sort by execution accuracy
    final_report = taxonomy_summary.sort_values(by='ex_acc', ascending=False)
    print(final_report.to_string())
    
# To run the script on its own manually
if __name__ == "__main__":
    print_taxonomyReport(None)