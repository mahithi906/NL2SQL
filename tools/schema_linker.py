import json  # To parse LLM Responses
from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv  # To load environmnrt variables

from metadata.metadata_loader import get_tables
from config.settings import load_azure_settings

load_dotenv()
settings = load_azure_settings()


@tool
def schema_linker(question: str, short_term_history: list | None = None) -> dict:
    """
    Schema linker tool that identifies relevant tables and columns from a natural language question.

    Takes a user question and returns the database tables and columns that are relevant to answering it,
    including descriptions and sample values.
    Uses keyword matching and LLM fallback for robust schema grounding.

    Args:
        question: The user's natural language question about the data
        short_term_history: Optional short-term conversation history from the agent

    Returns:
        Dictionary with 'tables' (list of dicts with name and description) and 'columns' (dict mapping table names to list of column dicts with name, description, data_type, sample_values)
    """

    question_raw = question.strip()  # To prevent empty questions
    if not question_raw:
        return {"tables": [], "columns": {}, "error": "Empty question"}

    # Load table and coloumns metadata
    metadata = get_tables()
    real_tables = list(metadata.keys())
    real_columns = {t: [c["name"] for c in metadata[t]["columns"]] for t in real_tables}

    # full metadata of descriptin and smaple values for better understanding
    full_metadata = {}
    for table_name, table_info in metadata.items():
        full_metadata[table_name] = {
            "description": table_info["description"],
            "columns": {
                col["name"]: {
                    "description": col["description"],
                    "data_type": col["data_type"],
                    "sample_values": col["sample_values"],
                }
                for col in table_info["columns"]
            },
        }

    # Preparing history
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
- Include ALL descriptions and sample values for selected tables and columns from the metadata.
- Do NOT generate SQL.
- Return ONLY the relevant tables and columns details with full metadata.
- Use metadata verbatim with no alterations.
- If no match is found, return:
    “No relevant tables or columns found for the given question.”

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
OUTPUT FORMAT (STRICT)
------------------------------------------------------------
Return ONLY valid JSON in the form:

{
  "tables": [
    {
      "name": "Table1",
      "description": "Table description here"
    },
    {
      "name": "Table2", 
      "description": "Table description here"
    }
  ],
  "columns": {
    "Table1": [
      {
        "name": "ColumnA",
        "description": "Column description here",
        "data_type": "data type here",
        "sample_values": "sample values here"
      },
      {
        "name": "ColumnB",
        "description": "Column description here", 
        "data_type": "data type here",
        "sample_values": "sample values here"
      }
    ],
    "Table2": [
      {
        "name": "ColumnX",
        "description": "Column description here",
        "data_type": "data type here", 
        "sample_values": "sample values here"
      }
    ]
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
  "tables": [
    {
      "name": "PurchaseOrderDetail",
      "description": "Stores detailed line‑items of vendor purchase orders, including ordered quantities, unit cost, received quantities, rejected quantities, and extended cost calculations."
    }
  ],
  "columns": {
    "PurchaseOrderDetail": [
      {
        "name": "ReceivedQty",
        "description": "Units actually received against this line.",
        "data_type": "decimal",
        "sample_values": "[2.00,3.00,20.00,51.00,57.00]"
      },
      {
        "name": "ProductID", 
        "description": "Foreign key to the product being purchased.",
        "data_type": "int",
        "sample_values": "[1,2,4,317,318]"
      },
      {
        "name": "PurchaseOrderDetailID",
        "description": "Primary key (within the PO) for this line item.",
        "data_type": "int", 
        "sample_values": "[1,2,3,4,5]"
      }
    ]
  }
}

User: "How many work orders exist for product CA-5965?"
Output:
{
  "tables": [
    {
      "name": "Product",
      "description": "Contains the master list of manufactured and purchased products, including product attributes, pricing, dimensions, classifications, and lifecycle information."
    },
    {
      "name": "WorkOrder",
      "description": "Represents manufacturing work orders describing which product to build, the quantity required, production dates, and related scrap or scheduling details."
    }
  ],
  "columns": {
    "Product": [
      {
        "name": "ProductID",
        "description": "Primary key; unique identifier for each product record.",
        "data_type": "int",
        "sample_values": "[1,2,3,4,316]"
      },
      {
        "name": "ProductNumber",
        "description": "Manufacturer’s internal product code (SKU/part number).",
        "data_type": "nvarchar",
        "sample_values": "["AR-5381","BA-8327","BB-7421","BB-8107","BB-9108"]"
      }
    ],
    "WorkOrder": [
      {
        "name": "ProductID",
        "description": "Foreign key to the product being manufactured on this work order.",
        "data_type": "int",
        "sample_values": "[3,316,324,327,328]"
      }
    ]
  }
}

"""

    # Build final LLM prompt
    system_prompt = (
        f"{SCHEMA_GROUNDING_AGENT_PROMPT}\n\n"
        "Full Metadata:\n"
        f"{json.dumps(full_metadata, indent=2)}\n\n"
        "This is the conversation history and the current question:\n"
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

    # Return the LLM's enriched output directly
    result = {"tables": parsed.get("tables", []), "columns": parsed.get("columns", {})}
    return json.dumps(result)
