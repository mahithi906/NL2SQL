import json
from typing import Dict, Any
from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv
from config.settings import load_azure_settings

load_dotenv()
settings = load_azure_settings()


@tool
def sql_synthesis(
    question: str,
    tables: list,
    columns: dict | None = None,
    short_term_history: list | None = None,
) -> dict:
    """
    Generates a SQL query based on the question and relevant tables/columns.

    Parameters:
        question: user natural-language question
        tables: list of relevant tables (from schema_linker)
        columns: dict mapping table -> list of columns
    Returns:
        {
            "sql": "<generated SQL>"
        }
    """

    system_prompt = """

You are an NL2SQL SQL generation specialist. Your task is to produce EXACT, VALID, SQLite-compatible SQL queries using ONLY the tables and columns explicitly provided.

STRICT RULES:
- Use ONLY the provided tables and columns.
- Table names and column names MUST match EXACTLY as provided.
- Maintain original case of every identifier.
- SELECT queries ONLY.
- NEVER invent, guess, or modify tables or columns.
- Output MUST be a clean SQL SELECT statement with no markdown, no code fences, and no explanations.

DO NOT:
- rename, alias, or transform identifiers.
- hallucinate relationships or join keys.
- produce partial SQL or commentary.
- infer joins unless BOTH tables share an identical column name.

------------------------------------------------------------
JOIN COMPLETENESS (MANDATORY)
------------------------------------------------------------
If MORE THAN ONE table is required:
- Include join conditions ONLY using columns that exist *identically* in both tables.
- Maintain exact names and casing.
- No inferred or assumed join keys.

------------------------------------------------------------
FILTERING RULES
------------------------------------------------------------
- Text values → wrap in single quotes.
- Numbers → no quotes.
- Dates → use: date(column) = 'YYYY-MM-DD'.

------------------------------------------------------------
OUTPUT FORMAT (STRICT)
------------------------------------------------------------
Return ONLY a valid SQL SELECT query.

------------------------------------------------------------
EXAMPLES (MUST FOLLOW THIS STYLE)
------------------------------------------------------------

Example 1:
User: "Show the ReceivedQty for ProductID 530 in PurchaseOrderDetailID 4?"
Output:
SELECT ReceivedQty
FROM PurchaseOrderDetail
WHERE ProductID = 530 AND PurchaseOrderDetailID = 4
LIMIT 100;

Example 2:
User: "How many work orders exist for product CA-5965?"
Output:
SELECT COUNT(*)
FROM WorkOrder
JOIN Product ON WorkOrder.ProductID = Product.ProductID
WHERE Product.ProductNumber = 'CA-5965';

------------------------------------------------------------

If unsure, return the simplest correct SELECT query that satisfies the question.
"""

    # Safety: schema empty → cannot generate SQL
    if not tables or not columns:
        return {"sql": "", "error": "No schema available for SQL generation"}

    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    schema_json = json.dumps({"tables": tables, "columns": columns}, indent=2)

    user_prompt = f"""
User Question:
{question}

{history_text}Schema (JSON):
{schema_json}

Return ONLY the SQL SELECT query:
"""

    llm = azure_llm
    try:
        raw = llm.invoke(system_prompt + "\n" + user_prompt)
        response = raw.content.strip()
    except Exception as e:
        return {"sql": "", "error": f"Azure OpenAI error: {str(e)}"}

    sql = (
        response.replace("```sql", "").replace("```", "").strip().strip('"').strip("'")
    )

    return {"sql": sql}
