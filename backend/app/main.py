# Path: backend/app/main.py
# Main entry point for the NL2SQL application
import os
from dotenv import load_dotenv
from src.nl2sql.hf_engine import get_models, DEFAULT_MODEL_ID
from src.scripts.interactive_mode import run_interactiveMode
from src.scripts.evaluation_mode import run_evaluation

load_dotenv()
# Load HuggingFace API token from environment variable
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("HuggingFace API token not found!")

def select_model() -> str:
    """
    Allow user to choose NL2SQL models available.
    """
    available_models = get_models()
    print("\n" + "="*30)
    print(" Select Model for Testing:")
    print("\n***Press q to quit at any time.")
    print("\n" + "="*30)

    for i, model in enumerate(available_models, 1):
        print(f"{i}. {model}")
    print(f"{len(available_models) + 1}. Use Default [Recommended]: ({DEFAULT_MODEL_ID})")
    print("\n" + "-"*50)

    while True:
        choice = input(f"Select a model (1-{len(available_models) + 1}) or 'q' to quit: ")

        if choice.lower() == 'q':
            print("Returning to main menu.")
            return None
        
        try:
            choice = int(choice)

            if 1 <= choice <= len(available_models):
                selected = available_models[choice-1]
                print(f"\n[+] Active Model set to: {selected}")
                return selected
            elif choice == len(available_models) + 1:
                print(f"\n[+] Active Model set to Default: {DEFAULT_MODEL_ID}")
                return DEFAULT_MODEL_ID
            else:
                print("Invalid range. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a number corresponding to the model choice.")

def main():
    """Main application entry point and interactive menu"""
    while True:
        print("\n" + "="*30)
        print(" NL2SQL Application Main Menu")
        print("\n" + "="*30)
        print("1. Run Interactive Agent NL2SQL Mode (Question Answering Evaluation)")
        print("2. Run Batch Evaluation of NL2SQL Agent (Question to SQL Evaluation)")
        print("3. Exit")
        print("\n" + "="*30)
        
        choice = input("Select an option (1-3): ")

        if choice == '1':
            selected_model = select_model()
            if selected_model:
                run_interactiveMode(model_id=selected_model)
        elif choice == '2':
            selected_model = select_model()
            if selected_model:
                run_evaluation(model_id=selected_model)
        elif choice == '3':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option (1, 2, or 3).")

if __name__ == "__main__":
    main()