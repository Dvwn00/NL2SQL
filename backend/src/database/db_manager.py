# Path: src/database/db_manager.py
# This module provides a function to establish a connection to the SQLite database.
# Include a RAG-based dynamic schema retrieval.
import os
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# The path to SQLite database
DB_PATH = os.getenv("SQLITE_DB_PATH", "src/database/Chinook_Sqlite.sqlite")
DB_URI = f"sqlite:///{DB_PATH}"

# Define RAG table description as knowledge base
TABLE_DESCRIPTIONS = [
    Document(page_content="Contains music albums associated with artists", metadata={"table_name": "Album"}),
    Document(page_content="Contains information about artists", metadata={"table_name": "Artist"}),
    Document(page_content="Contains customer information like name, address, phone, and email", metadata={"table_name": "Customer"}),
    Document(page_content="Contains employee information such as name, title, hire date, and manager", metadata={"table_name": "Employee"}),
    Document(page_content="Contains musical genres like Rock, Jazz, or Metal", metadata={"table_name": "Genre"}),
    Document(page_content="Contains details of invoices including billing information and total amount", metadata={"table_name": "Invoice"}),
    Document(page_content="Contains line items for each invoice, linking to the purchased tracks.", metadata={"table_name": "InvoiceLine"}),
    Document(page_content="Contains media types like MPEG audio or AAC audio.", metadata={"table_name": "MediaType"}),
    Document(page_content="Contains custom playlists created by users.", metadata={"table_name": "Playlist"}),
    Document(page_content="Mapping table linking tracks to playlists.", metadata={"table_name": "PlaylistTrack"}),
    Document(page_content="Contains details of music tracks including name, album, genre, and composer", metadata={"table_name": "Track"}),
]

# Initialize Chroma vector store with HuggingFace embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Chroma vector store with a persistent directory for storing embeddings
vector_store = Chroma.from_documents(
    documents = TABLE_DESCRIPTIONS,
    embedding = embedding_model,
    persist_directory = "chroma_db"
)

# Get a connection to the SQLite database
def get_db_connection():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Retrieve relevant schema context based on the user's question
def get_relevant_tables(question: str, top_k: int = 4) -> list:
    """
    RAG function: Retrieves the most relevant table descriptions based on the user's question.
    """
    # Perform a similarity search in vector store
    docs = vector_store.similarity_search(question, k=top_k)

    # Extract table names from the retrieved documents
    relevant_tables = [doc.metadata["table_name"] for doc in docs]
    return relevant_tables

# Get database schema context
def get_schema_context(question=None):
    """
    Returns the DDL and sample rows.
    If a question is provided, it retrieves the most relevant tables based on the question and returns their schema information.
    """
    try:
        tables_to_include = None

        # Trigger RAG retrieval if a question is provided
        if question:
            tables_to_include = get_relevant_tables(question)
            print(f"RAG selected tables for question '{question}': {tables_to_include}")
        
        # Connect to the database and retrieve schema information
        db = SQLDatabase.from_uri(DB_URI, include_tables = tables_to_include, sample_rows_in_table_info=5)
        return db.get_table_info()
    except Exception as e:
        return f"Error retrieving database schema: {e}"