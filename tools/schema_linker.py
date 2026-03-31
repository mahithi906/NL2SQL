import json
from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv

from metadata.metadata_loader import get_tables
from config.settings import load_azure_settings

load_dotenv()
settings = load_azure_settings()


@tool
def schema_linker(question: str, short_term_history: list | None = None) -> dict:
    """
    Schema linker tool that identifies relevant tables and columns from a natural language question.

    Takes a user question and returns the database tables and columns that are relevant to answering it.
    Uses keyword matching and LLM fallback for robust schema grounding.

    Args:
        question: The user's natural language question about the data
        short_term_history: Optional short-term conversation history from the agent

    Returns:
        Dictionary with 'tables' (list) and 'columns' (dict mapping tables to columns)
    """

    question_raw = question.strip()
    if not question_raw:
        return {"tables": [], "columns": {}, "error": "Empty question"}

    # Load metadata (raw, untouched)
    metadata = get_tables()
    real_tables = list(metadata.keys())
    real_columns = {t: [c["name"] for c in metadata[t]["columns"]] for t in real_tables}

    # Prepare history (optional)
    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "\nPrevious conversation:\n" + "\n".join(lines) + "\n"

    SCHEMA_GROUNDING_AGENT_PROMPT = """
You are a metadata specialist. Identify the exact tables and columns required to answer the user’s question using ONLY the metadata provided.

STRICT RULES:
- Use metadata EXACTLY as returned.
- Reproduce table names and column names verbatim.
- Select ONLY the tables and columns strictly required to answer the question.
- Output must contain ONLY actual tables and columns present in metadata.

DO NOT:
- rename, alias, normalize, or modify any identifier.
- add or remove prefixes or suffixes.
- infer relationships, foreign keys, joins, or business logic.
- generate SQL, pseudo-SQL, or explanations.
- hallucinate missing tables or columns.

------------------------------------------------------------
CASE PRESERVATION (MANDATORY)
------------------------------------------------------------
- Table names and column names MUST be returned in the EXACT SAME CASE as in metadata.
- Do NOT change casing in any form:
    • camelCase ↔ snake_case
    • lowercase ↔ uppercase
    • mixedCase ↔ lowercase
- Treat all identifiers as case-sensitive.
- Any result that alters casing is INVALID.

------------------------------------------------------------
JOIN COMPLETENESS (MANDATORY)
------------------------------------------------------------
If MORE THAN ONE TABLE is selected:
- Include the join column(s) from EACH table.
- Join columns are those with the SAME name across tables.
- Do NOT rename, infer, map, or explain joins.
- Only include join columns that literally exist in the metadata.

------------------------------------------------------------
DATE HANDLING (MANDATORY)
------------------------------------------------------------
- If the user question references time such as:
“today”, “yesterday”, “current”, “latest”, “now”, “real-time”, “live”  or similar temporal synonyms,
 you MUST include the date or datetime column(s)
exactly as defined in metadata.
- Do NOT infer date ranges.
- Do NOT rename or transform date fields.
- IMPORTANT: Tables named with "live_data" (e.g., factory_gl_fct_ypo_live_data)
must ONLY be selected when the user's date is exactly today (2025-11-16).
For any other date (past, specific, or unspecified), use historical/metrics views.

------------------------------------------------------------
OUTPUT FORMAT (STRICT)
------------------------------------------------------------
Return ONLY valid JSON in the form:

{
  "tables": ["Table1", "Table2"],
  "columns": {
      "Table1": ["ColumnA", "ColumnB"],
      "Table2": ["ColumnX"]
  }
}

If no match is found, return exactly:
{"tables": [], "columns": {}}

------------------------------------------------------------
EXAMPLES
------------------------------------------------------------
User: "Show the ReceivedQty for ProductID 530 in PurchaseOrderDetailID 4?"
Output:
{
  "tables": ["PurchaseOrderDetail"],
  "columns": {
      "PurchaseOrderDetail": ["ReceivedQty", "ProductID", "PurchaseOrderDetailID"]
  }
}

User: "How many work orders exist for product CA-5965?"
Output:
{
  "tables": ["Product", "WorkOrder"],
  "columns": {
      "Product": ["ProductID", "ProductNumber"],
      "WorkOrder": ["ProductID"]
  }
}
--------------------------------------------------------------
Rules:
--------------------------------------------------------------

    - Do NOT generate SQL.
    - Return ONLY the relevant tables and columns details.
    - Use metadata verbatim with no alterations.
    - If no match is found, return:
      “No relevant tables or columns found for the given question.”
"""

    # Build final LLM prompt
    system_prompt = (
        f"{SCHEMA_GROUNDING_AGENT_PROMPT}\n\n"
        "Metadata Tables:\n"
        f"{json.dumps(real_tables, indent=2)}\n\n"
        "Metadata Columns:\n"
        f"{json.dumps(real_columns, indent=2)}\n\n"
        f"{history_text}\n"
        "User Question:\n"
        f"{question_raw}\n\n"
        "Return JSON ONLY."
    )

    # Call Azure LLM
    try:
        llm_response = azure_llm.invoke(system_prompt)
        parsed = json.loads(llm_response.content)
    except Exception:
        return {"tables": [], "columns": {}}

    # Final output
    return {"tables": parsed.get("tables", []), "columns": parsed.get("columns", {})}
