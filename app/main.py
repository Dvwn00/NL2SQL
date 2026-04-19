# Path: app/main.py
# Main entry point for the NL2SQL application
import os
from dotenv import load_dotenv
from src.nl2sql.sql_agent import nl2sql_agent
from src.scripts.evaluate_hf import run_evaluation

load_dotenv()

# User prompt question manually and see the agent's response
def interactive_mode():
    """Allows user to manually type questions and get agent's response."""
    print("\n========= Interactive NL2SQL Mode =========")
    print("Type 'exit' or 'q' to return to the main menu.\n")

    while True:
        question = input("\nEnter your question: ")
        if question.lower() in ['exit', 'q']:
            break
        if not question.strip():
            continue

        print("\nProcessing your question...")
        response = nl2sql_agent(question)

        print("\n========= Agent Response =========")
        print(f"Status: {response.get('status')}")
        print(f"Generated SQL:\n{response.get('query')}")

        if response.get('status') == 'success':
            print(f"\nresults (First 5 rows):\n{response.get('results')[:5]}")
        else:
            print(f"\nError Details:\n{response.get('error')}")
        print("==================================\n")

def main():
    """Main application entry point and interactive menu"""
    while True:
        print("\n" + "="*30)
        print(" NL2SQL Application Main Menu")
        print("\n" + "="*30)
        print("1. Run Interactive Agent NL2SQL Mode (Ask a single question)")
        print("2. Run Batch Evaluation of NL2SQL Agent (Evaluate on 15 test cases)")
        print("3. Exit")
        print("\n" + "="*30)
        
        choice = input("Select an option (1-3): ")

        if choice == '1':
            interactive_mode()
        elif choice == '2':
            run_evaluation()
        elif choice == '3':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option (1, 2, or 3).")

if __name__ == "__main__":
    main()