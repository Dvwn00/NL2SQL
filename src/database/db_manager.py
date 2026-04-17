#"""Database helpers for the NL2SQL project."""

import os
import re
import sqlite3
from typing import Dict, List


DB_PATH = os.path.join(os.path.dirname(__file__), "Chinook_Sqlite.sqlite")
STOPWORDS = {
    "a",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "count",
    "each",
    "find",
    "for",
    "from",
    "give",
    "has",
    "have",
    "how",
    "in",
    "is",
    "list",
    "many",
    "most",
    "name",
    "names",
    "of",
    "on",
    "show",
    "the",
    "their",
    "there",
    "to",
    "total",
    "what",
    "which",
    "who",
    "with",
}


def get_db_connection():
    """Establish a connection to the SQLite database."""
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as error:
        print(f"Error connecting to database: {error}")
        return None


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {token for token in tokens if token not in STOPWORDS}


def _quote_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def _load_schema_metadata(connection: sqlite3.Connection) -> Dict[str, Dict[str, object]]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )

    metadata: Dict[str, Dict[str, object]] = {}
    for row in cursor.fetchall():
        table_name = row["name"]
        quoted_table = _quote_identifier(table_name)

        columns = cursor.execute(f"PRAGMA table_info({quoted_table})").fetchall()
        foreign_keys = cursor.execute(f"PRAGMA foreign_key_list({quoted_table})").fetchall()

        metadata[table_name] = {
            "ddl": row["sql"] or "",
            "columns": [
                {
                    "name": column["name"],
                    "type": column["type"] or "TEXT",
                    "notnull": bool(column["notnull"]),
                    "pk": bool(column["pk"]),
                }
                for column in columns
            ],
            "foreign_keys": [
                {
                    "from": foreign_key["from"],
                    "to_table": foreign_key["table"],
                    "to_column": foreign_key["to"],
                }
                for foreign_key in foreign_keys
            ],
        }

    return metadata


def _build_table_summary(table_name: str, table_info: Dict[str, object]) -> str:
    column_parts = []
    for column in table_info["columns"]:
        tags = []
        if column["pk"]:
            tags.append("PK")
        if column["notnull"]:
            tags.append("NOT NULL")

        tag_suffix = f" [{' '.join(tags)}]" if tags else ""
        column_parts.append(f"{column['name']} {column['type']}{tag_suffix}")

    summary = f"Table {table_name}: {', '.join(column_parts)}"
    if table_info["foreign_keys"]:
        relationships = ", ".join(
            f"{table_name}.{foreign_key['from']} -> "
            f"{foreign_key['to_table']}.{foreign_key['to_column']}"
            for foreign_key in table_info["foreign_keys"]
        )
        summary = f"{summary}\nRelationships: {relationships}"

    return summary


def _rank_tables(
    metadata: Dict[str, Dict[str, object]], question: str | None, max_tables: int
) -> List[str]:
    table_names = list(metadata.keys())
    if not question:
        return table_names

    question_tokens = _tokenize(question)
    if not question_tokens:
        return table_names

    scored_tables = []
    for table_name, table_info in metadata.items():
        table_tokens = _tokenize(table_name)
        column_tokens = set()
        for column in table_info["columns"]:
            column_tokens.update(_tokenize(column["name"]))

        score = 0
        score += 4 * len(question_tokens & table_tokens)
        score += 2 * len(question_tokens & column_tokens)

        singular_name = table_name[:-1].lower() if table_name.lower().endswith("s") else ""
        if singular_name and singular_name in question.lower():
            score += 2
        if table_name.lower() in question.lower():
            score += 3

        scored_tables.append((score, table_name))

    scored_tables.sort(key=lambda item: (-item[0], item[1]))
    selected = [table_name for score, table_name in scored_tables if score > 0][:max_tables]

    if not selected:
        selected = [table_name for _, table_name in scored_tables[:max_tables]]

    # Pull in directly related tables so the model sees valid join paths.
    expanded = list(selected)
    for table_name in selected:
        for foreign_key in metadata[table_name]["foreign_keys"]:
            related_table = foreign_key["to_table"]
            if related_table in metadata and related_table not in expanded:
                expanded.append(related_table)

    for table_name, table_info in metadata.items():
        for foreign_key in table_info["foreign_keys"]:
            if foreign_key["to_table"] in selected and table_name not in expanded:
                expanded.append(table_name)

    return expanded[: max(max_tables, len(expanded))]


def get_schema_context(question: str | None = None, max_tables: int = 7) -> str:
    """Extract schema information for prompt construction.

    When a question is provided, the returned schema is narrowed to the most
    relevant tables plus their immediate relationships. This keeps prompts
    smaller while preserving valid join paths.
    """

    connection = get_db_connection()
    if not connection:
        return "Unable to connect to the database to retrieve schema information."

    try:
        metadata = _load_schema_metadata(connection)
    finally:
        connection.close()

    selected_tables = _rank_tables(metadata, question, max_tables=max_tables)
    schema_sections = [_build_table_summary(table_name, metadata[table_name]) for table_name in selected_tables]

    all_relationships = []
    for table_name in selected_tables:
        for foreign_key in metadata[table_name]["foreign_keys"]:
            if foreign_key["to_table"] in selected_tables:
                all_relationships.append(
                    f"{table_name}.{foreign_key['from']} = "
                    f"{foreign_key['to_table']}.{foreign_key['to_column']}"
                )

    if all_relationships:
        schema_sections.append("Join paths:\n" + "\n".join(sorted(set(all_relationships))))

    return "\n\n".join(schema_sections)


if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        print("Database connection successful!")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Tables in the database:", [row[0] for row in cursor.fetchall()])
        connection.close()
    else:
        print("Failed to connect to the database.")
