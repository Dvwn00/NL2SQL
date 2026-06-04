---
title: NL2SQL API
emoji: 🗄️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

👋🏻 The Streamlit UI development has been done, try the demo now!

👉🏻 NL2SQL Demo: https://nl2sql-assistant-dvwn.streamlit.app/

# NL2SQL
A backend Command Line Interface (CLI) framework designed to evaluate and test various NL2SQL models.

**Note:** The frontend interface for this application is currently in progress and not yet available. All interactions are handled via the CLI.

## Prerequisites & Installation

To run this CLI tool locally, follow these steps to set up your environment:

1. Activate the Virtual Environment.

- **Windows**: venv\Scripts\Activate
- **macOS/Linux**: source venv/bin/activate

2. Install Requirements
- Ensure a *requirements.txt* file exists in your project backend folder.

    > pip install -r requirements.txt

3. Configure Environment Variable (.env)

**Note:** Users must generate your own free access token from your https://huggingface.co/settings/tokens to avoid rate limits.
    
- Create a *.env* file in the *backend/* directory

- Add your Hugging Face *Read* Token to the file.

    > HF_TOKEN=your_hugging_face_read_token_here

## Usage Guide

Once your environment is set up and your token is configured, you can run the CLI application.

1. Navigate to the Backend Directory

    > cd backend

2. Launch the Application

    > python -m app.main

3. Interacting with the CLI Menu Upon running the command, you will be presented with a main menu. Choose the number corresponding to your desired action:

    1. Running Question to SQL Test: Evaluates how well a model translates natural language queries into executable SQL commands.

    2. Running Question Answering Test: Evaluates the end-to-end process (Question -> SQL -> Database Execution -> Natural Language Answer).

    3. Exit/Quit: Closes the application.

4. Model Selection & Batch Testing

    1. After selecting either option 1 or 2, the CLI will display a list of available NL2SQL models.

    2. Enter the number/name of the model you wish to test.

    3. Automatic Execution: Once a model is selected, the system will automatically begin running the batch test against the scenarios defined in scripts/test_cases.json. Sit back and wait for the reports to generate in your root folder!

## 🚧 Roadmap
✅ Development and integration of a graphical User Interface (Frontend).

- Additional database schema support.
