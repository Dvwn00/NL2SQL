# Path: app/main.py
# Main entry point for the NL2SQL application
import os
from dotenv import load_dotenv
from src.scripts.interactive_mode import run_interactiveMode
from src.scripts.evaluation_mode import run_evaluation

load_dotenv()
# Load HuggingFace API token from environment variable
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("HuggingFace API token not found!")

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
            run_interactiveMode()
        elif choice == '2':
            run_evaluation()
        elif choice == '3':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option (1, 2, or 3).")

if __name__ == "__main__":
    main()