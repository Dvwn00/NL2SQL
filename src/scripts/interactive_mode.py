# Path: src/scripts/interactive_mode.py
# Interactive mode: Allows user to manually type questions and see the agent's response
from src.nl2sql.sql_agent import nl2sql_agent

def run_interactiveMode():
    """ Allows user to manually type questions and get agent's response."""
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
        if response.get('status') == 'success':
            print(f"Answer: {response.get('nl_response')}\n")
            print(f"Generated SQL:\n{response.get('query')}\n")
        else:
            print(f"Status: {response.get('status')}")
            print(f"Generated SQL:\n{response.get('query')}")
            print(f"\nError Details:\n{response.get('error')}")
        print("==================================\n")