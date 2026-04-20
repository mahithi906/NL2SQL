from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv
from config.settings import load_azure_settings

load_dotenv()
settings = load_azure_settings()


@tool
def answering_agent(
    question: str,
    rows: list | None = None,
    row_count: int = 0,
    short_term_history: list | None = None,
) -> dict:
    """
    Converts SQL executor results into a natural-language answer.

    Parameters:
        question: user question (string)
        rows: SQL result rows (list of dicts) - optional
        row_count: number of rows (int)
        short_term_history: Optional short-term conversation history

    Returns:
        {
            "answer": "<natural language answer>"
        }

    Behavior:
    - Provides natural-language summary of results
    - Uses conversation history for context
    """

    if rows is None:
        rows = []

    # --- History ---
    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"
        print(f"[ANSWERING_AGENT] Using {len(short_term_history)} history items")

    system_prompt = """
You are a conversational data assistant.

STRICT RULES:
- DO NOT mention SQL, tables, databases, schema or rows.
- DO NOT describe internal processing.
- Speak naturally and conversationally.
- Provide a smooth explanation of the results.
- USE the previous conversation history to understand context.

"""

    user_prompt = f"""
User Question:
{question}

{history_text}
Here is the raw data (JSON):
{rows}

There are {row_count} results.

Explain the answer clearly in natural language, with no technical wording.
"""

    raw = azure_llm.invoke(system_prompt + "\n" + user_prompt)
    return {"answer": raw.content.strip()}
