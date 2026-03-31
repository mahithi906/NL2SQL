from langchain.tools import tool
from config.azure_client import azure_llm
from dotenv import load_dotenv
from config.settings import load_azure_settings

load_dotenv()
settings = load_azure_settings()


@tool
def answering_agent(
    question: str, rows: list, row_count: int, short_term_history: list | None = None
) -> dict:
    """
    Converts SQL executor results into a natural-language answer.

    Parameters:
        question: user question (string)
        rows: SQL result rows (list of dicts)
        row_count: number of rows (int)
        short_term_history: Optional short-term conversation history from the agent

    Returns:
        {
            "answer": "<natural language answer>"
        }

    Behavior:
    - If data exists → summarize results
    - If no data → explain no data found
    """

    # --- History ---
    history_text = ""
    if short_term_history:
        lines = [f"- {msg.content}" for msg in short_term_history]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    system_prompt = """
You are a conversational data assistant.

STRICT RULES:
- DO NOT mention SQL, tables, databases, schema or rows.
- DO NOT describe internal processing.
- DO NOT output lists, bullet points, or structured formats.
- DO NOT repeat field names unless necessary.
- Speak naturally and conversationally.
- Provide a smooth explanation of the results.
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
