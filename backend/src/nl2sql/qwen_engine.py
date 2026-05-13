# Inference Script for Qwen-2.5:1B via ollama

import requests
import json

def query_qwen(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt,
        "stream": False,
        "options": {
            # Set temperature to 0 for deterministic output
            "temperature": 0
        }
    }
    response = requests.post(url, json=payload)
    raw_response = response.json().get("response", "").strip()

    # Clean the response to extract only the SQL query
    if raw_response.startswith("```sql") and raw_response.endswith("```"):
        return raw_response.replace("```sql", "").replace("```", "").strip()
    else:
        return raw_response 

def build_qwen_prompt(question, schema):
    return f"""## Instructions:
    You are an expert SQLite assistant that converts natural language questions into SQL queries.

    Use ONLY SQLite syntax.

    Important database relationships:
    - Artist(ArtistId) -> Album(ArtistId)
    - Album(AlbumId) -> Track(AlbumId)
    - Track(GenreId) -> Genre(GenreId)
    - Track(MediaTypeId) -> MediaType(MediaTypeId)
    - Track(TrackId) -> InvoiceLine(TrackId)
    - InvoiceLine(InvoiceId) -> Invoice(InvoiceId)
    - Customer(CustomerId) -> Invoice(CustomerId)
    - Customer(SupportRepId) -> Employee(EmployeeId)
    - Playlist(PlaylistId) -> PlaylistTrack(PlaylistId)
    - PlaylistTrack(TrackId) -> Track(TrackId)

    SQL Rules:
    1. Use JOIN when data comes from multiple tables.
    2. Use GROUP BY when using COUNT, SUM, or AVG.
    3. Use HAVING for filtering aggregated values.
    4. Use ORDER BY for ranking results.
    5. Use LIMIT instead of TOP.
    6. Always produce executable SQLite SQL.
    7. Always use table aliases (t, a, ar, g, etc.) when joining tables.

    Return ONLY the SQL query.
    Do not provide explanations.

    ## Database Schema:
    {schema}

    ## Question:
    {question}

    ## SQL Query:
    """