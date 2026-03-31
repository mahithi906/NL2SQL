import re
from langchain.tools import tool


@tool
def sql_validator(sql: str) -> dict:
    """
    Regex-based SQL validator tool.

    Parameters:
        sql: the generated SQL query string

    Returns:
        {
            "validated_sql": "<valid sql or ''>",
            "error": "<error message or ''>"
        }

    Rules:
    - Query MUST start with SELECT
    - DELETE, UPDATE, INSERT, DROP, ALTER are forbidden
    """

    sql = sql or ""
    validated = ""
    error = ""

    # Ensure SQL starts with SELECT
    if not re.match(r"^\s*select\b", sql, flags=re.IGNORECASE | re.DOTALL):
        error = "Only SELECT queries are allowed."

    # Block dangerous SQL operations
    dangerous_keywords = [
        r"\binsert\b",
        r"\bupdate\b",
        r"\bdelete\b",
        r"\bdrop\b",
        r"\balter\b",
    ]

    if any(
        re.search(pattern, sql, flags=re.IGNORECASE) for pattern in dangerous_keywords
    ):
        error = "Query contains disallowed keywords."

    # If valid, allow SQL to pass through
    if not error:
        validated = sql

    return {"validated_sql": validated, "error": error}
