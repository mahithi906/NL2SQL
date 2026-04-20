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
    tables: list,  # list of tale names
    columns: (
        dict | None
    ) = None,  # dict of table -> columns witn descriptions,data type and sample values
    short_term_history: list | None = None,
) -> dict:
    """
    Generates a SQL query based on the question and relevant tables/columns.

    Parameters:
        question: user natural-language question
        tables: list of relevant tables with descriptions (from schema_linker)
        columns: dict mapping table -> list of columns with descriptions, data_types, sample_values
    Returns:
        {
            "sql": "<generated SQL>"
        }
    """

    system_prompt = """

You are an NL2SQL SQL generation specialist. Your task is to produce EXACT, VALID, SQLite-compatible SQL queries using ONLY the tables and columns explicitly provided.

The schema includes table descriptions, column descriptions, data types, and sample values. USE THESE DESCRIPTIONS AND SAMPLES to understand what each table and column represents and to generate appropriate SQL queries.

STRICT RULES:
- Use ONLY the provided tables and columns.
- Table names and column names MUST match EXACTLY as provided.
- Maintain original case of every identifier.
- SELECT queries ONLY.
- NEVER invent, guess, or modify tables or columns.
- Output MUST be a clean SQL SELECT statement with no markdown, no code fences, and no explanations.
- Use the table descriptions, column descriptions, data types, and sample values to guide your understanding of what each field means and how to filter or aggregate correctly.
- All text values must be enclosed in single quotes.
- Ensure every opening quote (') has a corresponding closing quote (').

DO NOT:
- rename, alias, or transform identifiers.
- hallucinate relationships or join keys.
- produce partial SQL or commentary.
- infer joins unless BOTH tables share an identical column name.

  
AGGREGATION RULE (MANDATORY)
------------------------------------------------------------
- If the query uses any aggregate function such as COUNT, SUM, AVG, MIN, MAX,
  or includes GROUP BY or HAVING clauses, DO NOT add a LIMIT clause.
- Aggregation queries must operate on the complete dataset unless the user
  explicitly asks to limit the results.
- LIMIT 100 is allowed ONLY for non-aggregate, row-level SELECT queries.

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
- Use sample values as reference for expected data formats and types.

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

Example 3:
User : what is the safety stock level for pdt AR-5381?
output:
SELECT SafetyStockLevel
FROM Product
WHERE ProductNumber = 'AR-5381'
LIMIT 100

Example 4:
User : list all the pdts with days to manufacture more than 0.
output : 
SELECT ProductNumber
FROM Product
WHERE DaysToManufacture > 0
LIMIT 100

Example 5 :
User : how many transactions occured for pdt 921?
output :
SELECT COUNT(*)
FROM TransactionHistory
WHERE ProductID = 921
LIMIT 100

Example 6 :
User : How many transactions happened on 21st may 2014 for product 873?
output :
SELECT COUNT(*) 
FROM TransactionHistory
WHERE ProductID = 873
  AND date(TransactionDate) = '2014-05-21'
LIMIT 100

Exmaple 7:
User : What is the name of Product ID 783, and how many units of it were sold?
output :
SELECT Product.Name, SUM(TransactionHistory.Quantity) AS UnitsSold
FROM Product
JOIN TransactionHistory ON Product.ProductID = TransactionHistory.ProductID
WHERE Product.ProductID = 783 AND TransactionHistory.TransactionType = 'S'
GROUP BY Product.Name
LIMIT 100

Example 8 :
User : How many work orders were created for Product ID 732 between June 1 and June 20, 2011?
output :
SELECT COUNT(*) 
FROM WorkOrder
WHERE ProductID = 732
  AND date(StartDate) >= '2011-06-01'
  AND date(StartDate) <= '2011-06-20'

Example 9 :
User : Which products have exactly 550 items in stock?
output :
SELECT Product.ProductNumber
FROM Product
JOIN PurchaseOrderDetail ON Product.ProductID = PurchaseOrderDetail.ProductID
GROUP BY Product.ProductID, Product.ProductNumber
HAVING SUM(PurchaseOrderDetail.StockedQty) = 550
LIMIT 100

Example 10 :
User : Which products take time to manufacture?
output :
Running: SELECT Name
FROM Product
WHERE DaysToManufacture > 0
LIMIT 100

------------------------------------------------------------

If unsure, return the simplest correct SELECT query that satisfies the question.
"""

    # Safety: schema empty → cannot generate SQL
    if not tables or not columns:
        return {"sql": "", "error": "No schema available for SQL generation"}

    # Normalize schema_linker output so the agent always receives full metadata
    normalized_tables = []
    for table in tables:
        if isinstance(table, str):
            normalized_tables.append({"name": table, "description": ""})
        else:
            normalized_tables.append(
                {
                    "name": table.get("name"),
                    "description": table.get("description", ""),
                }
            )

    normalized_columns = {}
    for table_name, cols in columns.items():
        normalized_columns[table_name] = []
        for col in cols:
            if isinstance(col, str):
                normalized_columns[table_name].append(
                    {
                        "name": col,
                        "description": "",
                        "data_type": "",
                        "sample_values": "",
                    }
                )
            else:
                normalized_columns[table_name].append(
                    {
                        "name": col.get("name"),
                        "description": col.get("description", ""),
                        "data_type": col.get("data_type", ""),
                        "sample_values": col.get("sample_values", ""),
                    }
                )

    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    # Format schema for better LLM understanding
    schema_text = "SCHEMA INFORMATION:\n\n"
    for table in normalized_tables:
        schema_text += f"Table: {table['name']}\n"
        schema_text += f"Table Description: {table['description']}\n"
        schema_text += "Columns:\n"
        for col in normalized_columns.get(table["name"], []):
            schema_text += f"  - Column Name: {col['name']}\n"
            schema_text += f"    Data Type: {col['data_type']}\n"
            schema_text += f"    Column Description: {col['description']}\n"
            schema_text += f"    Sample Values: {col['sample_values']}\n"
        schema_text += "\n"

    # using json
    schema_json = json.dumps(
        {"tables": normalized_tables, "columns": normalized_columns}, indent=2
    )

    user_prompt = f"""
User Question:
{question}

{history_text}{schema_text}
JSON Schema:
{schema_json}

Return ONLY the SQL SELECT query:
"""

    llm = azure_llm
    try:
        raw = llm.invoke(system_prompt + "\n" + user_prompt)
        response = raw.content.strip()
    except Exception as e:
        return {"sql": "", "error": f"Azure OpenAI error: {str(e)}"}

    sql = response.replace("```sql", "").replace("```", "").strip()

    return {"sql": sql}
