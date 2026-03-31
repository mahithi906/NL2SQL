import json
from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv

from config.settings import load_azure_settings
from metadata.metadata_loader import get_tables
from tools.state import STATE

load_dotenv()
settings = load_azure_settings()


@tool
def debug_agent(
    question: str,
    sql: str,
    execution_error: str,
    tables: list,
    columns: dict,
    short_term_history: list | None = None,
) -> dict:
    """
    SQL Debugging Tool with attempt-limit + bypass behavior.

    TRIGGERED WHEN:
        - SQL executor returns an execution error, OR
        - SQL executor returns zero rows

    DEBUGGING LOGIC:
        Attempt #1  → NO metadata
        Attempt #2  → WITH metadata
        Attempt #3  → WITH metadata
        Attempt #4+ → STOP debugging and return executor output
                         (execution_error & sql) directly to answering_agent.

    RETURN FORMATS:

        1) When debugging is active (attempts 1 to 3):
        {
            "corrected_sql": "<SQL string>",
            "attempt": <int>
        }

        2) When debugging exceeds limit (attempt > 3):
        {
            "bypass": True,
            "sql": "<original SQL>",
            "execution_error": "<executor error>"
        }
    """

    STATE.debug_triggered_times += 1
    attempt = STATE.debug_triggered_times

    if attempt > 3:
        return {"bypass": True, "sql": sql, "execution_error": execution_error}

    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    metadata_text = ""
    if attempt >= 2:
        tables_meta = get_tables()
        meta_lines = []

        for tbl, meta in tables_meta.items():
            desc = meta.get("description", "No description available.")
            col_list = ", ".join(col["name"] for col in meta["columns"])
            meta_lines.append(f"TABLE {tbl}: {desc}")
            meta_lines.append(f"  Columns: {col_list}\n")

        metadata_text = "\n".join(meta_lines)

    system_prompt = f"""
You are an elite SQL debugging expert.
Fix the broken SQL query using the rules below.

STRICT RULES:
- Return ONLY corrected SQL.
- No markdown.
- No explanations.
- Never invent tables or columns.
- Follow SQLite syntax.
- Always use LIMIT instead of TOP.

ATTEMPT INFO:
- Attempt #{attempt} of 3
- Attempt #1: No metadata
- Attempt #2: Metadata allowed
- Attempt #3: Metadata allowed
- Attempt #4+: STOP and return executor results
"""
    user_prompt = f"""
The SQL query failed.

User Question:
{question}

Broken SQL:
{sql}

Execution Error:
{execution_error}

Relevant Tables:
{tables}

Relevant Columns:
{columns}

{history_text}
"""

    if metadata_text:
        user_prompt += f"Metadata:\n{metadata_text}\n\n"
    user_prompt += "Return ONLY the corrected SQL."
    raw = azure_llm.invoke(system_prompt + "\n" + user_prompt)
    corrected_sql = raw.content.strip()
    corrected_sql = (
        corrected_sql.replace("```sql", "")
        .replace("```", "")
        .strip('"')
        .strip("'")
        .strip()
    )

    return {"corrected_sql": corrected_sql, "attempt": attempt}
