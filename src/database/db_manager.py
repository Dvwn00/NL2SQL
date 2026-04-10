# This module provides a function to establish a connection to the SQLite database used in the NL2SQL project. It also includes a test block to verify the connection and list the tables in the database.

import sqlite3
import os

# Get the path to the database file
DB_PATH = os.path.join(os.path.dirname(__file__), 'Chinook_Sqlite.sqlite')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        connection = sqlite3.connect(DB_PATH)
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None
    
# Test the database connection
if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        print("Database connection successful!")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Tables in the database:", cursor.fetchall())
        connection.close()
    else:
        print("Failed to connect to the database.")

# Extract Schema Information for LLM Prompts
def get_schema_context():
    """Extracts the database schema information to be used in LLM prompts."""
    connection = get_db_connection()
    if not connection:
        return "Unable to connect to the database to retrieve schema information."
    
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]

    schema_text = ""
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [f"{c[1]} ({c[2]})" for c in cursor.fetchall()]
        schema_text += f"Table {table}: {', '.join(columns)}\n"
    connection.close()
    return schema_text
    