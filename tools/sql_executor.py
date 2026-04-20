import os
import re
from typing import Dict, Any, List
from langchain.tools import tool
from sqlalchemy.exc import SQLAlchemyError
from langchain_community.utilities.sql_database import SQLDatabase

# REGEX HELPERS

_TRAILING_SEMI = re.compile(r";\s*$", flags=re.IGNORECASE)


def _strip_trailing_semicolon(sql: str) -> str:
    """Remove trailing semicolon."""
    return _TRAILING_SEMI.sub("", sql.strip())


# SQL EXECUTOR TOOL


@tool
def sql_executor(validated_sql: str) -> dict:
    """
    Execute a **validated SQL** query (SELECT-only) and return rows.

    Parameters:
        validated_sql: SQL string already checked by sql_validator

    Returns:
        {
            "executed": True/False,
            "rows": [...],
            "row_count": n,
            "execution_error": "<error or ''>"
        }
    """

    sql = validated_sql.strip()
    if not sql:
        return {
            "executed": False,
            "rows": [],
            "row_count": 0,
            "execution_error": "No validated SQL provided.",
        }

    rows: List[dict] = []
    row_count = 0
    execution_error = ""

    # Determine DB URL (defaults to bundled SQLite DB)
    database_url = os.getenv("DATABASE_URL")
    # if not present, default to the local SQLite DB
    if not database_url:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sqlite_path = os.path.join(project_root, "data", "adventureworks.sqlite3")
        database_url = f"sqlite:///{sqlite_path.replace(os.sep, '/')}"

    sql = _strip_trailing_semicolon(sql)

    # Execute SQL
    try:
        db = SQLDatabase.from_uri(database_url)

        print(f"[EXECUTOR] Connected to: {database_url}")
        print(f"[EXECUTOR] Running: {sql}")

        raw_result = db._execute(sql)

        # SQLAlchemy Result object
        if hasattr(raw_result, "keys"):
            columns = raw_result.keys()
            data = raw_result.fetchall()
            rows = [dict(zip(columns, row)) for row in data]

        # List fallback
        elif isinstance(raw_result, list):
            if raw_result and isinstance(raw_result[0], dict):
                rows = raw_result
            else:
                rows = [dict(enumerate(r)) for r in raw_result]

        row_count = len(rows)

    except SQLAlchemyError as e:
        execution_error = f"SQL Error: {str(e)}"
        print("[EXECUTOR] SQL ERROR:", execution_error)

    except Exception as e:
        execution_error = f"Execution Error: {str(e)}"
        print("[EXECUTOR] ERROR:", execution_error)

    # Return results
    return {
        "executed": execution_error == "",
        "rows": rows,
        "row_count": row_count,
        "execution_error": execution_error,
    }
