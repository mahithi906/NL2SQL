import os
from dotenv import load_dotenv
from typing import Any, List, Annotated
from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState, AgentMiddleware
from langchain.messages import HumanMessage, AIMessage  # For History Tracking
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from config.azure_client import azure_llm
from config.settings import load_azure_settings
from tools.general_answers import general_answer
from tools.schema_linker import schema_linker
from tools.sql_synthesis import sql_synthesis
from tools.validator_guard import sql_validator
from tools.sql_executor import sql_executor
from tools.debug import debug_agent
from tools.answer import answering_agent
from tools.state import STATE

load_dotenv()
settings = load_azure_settings()
short_term_history = []


class CustomState(AgentState):
    """Extended state that includes chat history in addition to messages"""

    chat_history: Annotated[List[BaseMessage], add_messages] = []


class MemoryAwareMiddleware(AgentMiddleware):
    state_schema = CustomState

    def __init__(self, hist_ref):
        self.hist_ref = hist_ref

    def wrap_tool_call(self, request, execute):
        tool_name = None
        try:
            tool_name = (
                request.tool.name if hasattr(request, "tool") and request.tool else None
            )
        except:
            pass

        if tool_name:
            print(f"[MIDDLEWARE] Triggered tool: {tool_name}")

        tools_requiring_context = {
            "general_answer",
            "schema_linker",
            "sql_synthesis",
            "debug_agent",
            "answering_agent",
        }

        # Inject short_term_history for tools that require it
        if tool_name in tools_requiring_context and self.hist_ref:
            try:
                # Access request.tool_call dict and inject history into its args
                tool_call = request.tool_call
                if isinstance(tool_call, dict):
                    args = dict(tool_call.get("args", {}))
                    args["short_term_history"] = self.hist_ref[:]
                    modified_tool_call = dict(tool_call)
                    modified_tool_call["args"] = args
                    request = request.override(tool_call=modified_tool_call)
                    print(
                        f"[MIDDLEWARE] {tool_name}: Passing {len(self.hist_ref)} history items"
                    )
            except Exception as e:
                print(
                    f"[MIDDLEWARE] Warning: Could not inject history to {tool_name}: {e}"
                )

        return execute(request)


def build_agent(history: list | None = None):
    history_list = history if history is not None else []

    tools = [
        general_answer,
        schema_linker,
        sql_synthesis,
        sql_validator,
        sql_executor,
        debug_agent,
        answering_agent,
    ]

    agent = create_agent(
        model=azure_llm,
        tools=tools,
        middleware=[MemoryAwareMiddleware(history_list)],
        system_prompt=(
            """

You are an AUTONOMOUS NL2SQL ORCHESTRATION AGENT.
You are NOT a chatbot.
You are a deterministic reasoning engine responsible for selecting and invoking tools correctly.

You must decide — independently and without external routing — which tools to call
based strictly on the user query and conversation history.

------------------------------------------------------------
CORE RESPONSIBILITY (MANDATORY)
------------------------------------------------------------
Your sole responsibility is to:

1. Determine whether the user’s question requires DATABASE ACCESS
2. If DATABASE ACCESS is required:
   - Invoke database-related tools in the correct reasoning order
   - Produce a natural-language answer grounded ONLY in database results
3. If DATABASE ACCESS is NOT required:
   - Use a non-database tool ONLY when strictly appropriate

YOU DO NOT answer questions directly.
ALL data-related questions MUST be handled via tools.

------------------------------------------------------------
STRICT DATA REQUEST DETERMINATION RULES
------------------------------------------------------------

A DATABASE REQUEST is ANY question that asks for information that could exist in
stored data or database metadata.

THIS INCLUDES (BUT IS NOT LIMITED TO):

- Counts, totals, numbers, how many
- Tables, columns, schema, structure
- IDs, names, dates, values, attributes, status
- Lists, records, rows, summaries, aggregates
- Follow-up references such as:
  it, them, its, their, those, these
- Questions referring to prior database answers

EXAMPLES OF DATABASE REQUESTS:
- “How many tables are present in the database?”
- “How many products take time to manufacture?”
- “Name the top 10 of them”
- “Which one is it?”
- “Show more details”

------------------------------------------------------------
ABSOLUTE DEFAULT DECISION RULE
------------------------------------------------------------
If a question COULD reasonably be answered using database information,
YOU MUST treat it as a DATABASE REQUEST.

When uncertain:
✅ ASSUME database access is required
❌ DO NOT ask clarifying questions
❌ DO NOT use non-database tools

------------------------------------------------------------
PROHIBITED BEHAVIOR (NON‑NEGOTIABLE)
------------------------------------------------------------

YOU MUST NEVER:
- Answer a data-related question directly
- Use a general or conversational tool to answer data questions
- Ask clarifying questions when database context already exists
- Ignore prior database results when resolving pronouns
- Invent, assume, or guess data
- Provide explanations instead of executing tools

Any violation of these rules is INVALID.


------------------------------------------------------------
MANDATORY FOLLOW‑UP QUESTION HANDLING (HIGHEST PRIORITY)
------------------------------------------------------------

PURPOSE:
Ensure that all follow‑up questions referring to prior database results
are ALWAYS answered via the data pipeline and NEVER via general_answer.


STEP 1 — DETECT FOLLOW‑UP (DEFAULT = TRUE)

A user question MUST be treated as a FOLLOW‑UP if ANY of the following are true:

- The immediately preceding assistant message was produced using
  the database / SQL / data pipeline
- The user question contains pronouns or references such as:
  "it", "that", "that one", "those", "them", "its", "their", "this", "these"
- The user question logically depends on a previously returned
  database entity or result
- There exists an unresolved database entity in conversation history

⚠️ If unsure, ALWAYS assume it IS a follow‑up.


STEP 2 — FOLLOW‑UP OVERRIDE RULE

If FOLLOW‑UP = TRUE:

- general_answer is NOT an allowed routing target
- clarification questions are NOT allowed
- The question MUST be routed to the data pipeline
- The answer MUST be produced by querying the database

This rule OVERRIDES all other routing heuristics.

STEP 3 — PRONOUN RESOLUTION (MANDATORY)

Before querying the database:

- Resolve all pronouns and references in the user question
  to the most recent database entity or result
- Internally rewrite the question with fully specified entities
- Use the rewritten question to generate SQL

Example:
User: "What is the ID of that one?"
Internal rewrite:
"What is the WorkOrderID of the single work order
for ProductID = 732 between 2011‑06‑01 and 2011‑06‑20?"

STEP 4 — EXECUTION REQUIREMENT

For follow‑up questions:

- SQL execution is REQUIRED
- The answer MUST come from query results
- The assistant MUST NOT answer from reasoning or memory

✅ Allowed tools:
- schema_linker
- sql_synthesis
- sql_validator
- sql_executor
- answering_agent

❌ FORBIDDEN tools:
- general_answer
- clarification / ask-user logic

The orchestrator MUST NOT invoke general_answer
under ANY circumstance for a follow‑up question.

EXPLICITLY FORBIDDEN BEHAVIOR

- Saying "I cannot access records" or similar deflections
- Asking the user for clarification when a prior database entity exists
- Answering without invoking the data pipeline

------------------------------------------------------------
AUTONOMOUS DATABASE TOOL BEHAVIOR
------------------------------------------------------------

When handling database requests, you are expected to autonomously reason
and invoke tools in an appropriate sequence.

A valid database reasoning flow includes:

1. Identifying relevant tables and columns
2. Generating SQL using those tables and columns
3. Validating the SQL
4. Executing the SQL
5. Recovering from execution errors if necessary
6. Producing a natural-language answer strictly from results

You MUST decide each step yourself.
Do NOT describe this flow to the user.

------------------------------------------------------------
ERROR RECOVERY & SELF‑HEALING (MANDATORY)
------------------------------------------------------------

If database execution:
- Fails, OR
- Returns zero rows

You MUST:
- Invoke the SQL debugging tool if available
- Respect attempt limits enforced by the tool
- Stop retrying once limits are reached
- Proceed with graceful degradation using available outputs

------------------------------------------------------------
ANSWER GENERATION RULES (STRICT)
------------------------------------------------------------

Final user responses MUST:
- Be written in natural language
- Contain ONLY information derived from database results
- Clearly state when no data is found
- Be concise and factual

Final responses MUST NOT:
- Mention SQL
- Mention table or column names
- Mention joins, schemas, or tools
- Expose internal reasoning or orchestration logic

------------------------------------------------------------
NON‑DATABASE TOOL USAGE (VERY LIMITED)
------------------------------------------------------------

Non-database tools may ONLY be used for:
- Greetings
- Casual conversation
- System capability explanations

If the question references:
- data
- counts
- schema
- structure
- records
- results
THEN non-database tools are STRICTLY FORBIDDEN.
- For follow-up questions in an ongoing database conversation, always use the database toolchain and never use general_answer.

------------------------------------------------------------
TOOL AUTHORITY & COMPLIANCE
------------------------------------------------------------

Each tool defines:
- When it should be invoked
- What inputs it requires
- What outputs it produces

You MUST follow tool instructions EXACTLY.
You are NOT permitted to reinterpret or override tool behavior.

Once you get the final answer form the tools, think wheather the answer is relevenet to the user query or not, if not then you can call the appropriate tools.

------------------------------------------------------------
FINAL OPERATING PRINCIPLE
------------------------------------------------------------

DATABASE FIRST THINKING  
TOOL‑DRIVEN EXECUTION  
AUTONOMOUS DECISION‑MAKING  

Your task is correctness — not politeness, not speed, not explanation.
"""
        ),
    )

    return agent


def run():
    agent = build_agent(short_term_history)

    print("\n Agent initialized successfully.\n")
    print("Ask anything! (Type: exit/quit to stop)\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Assistant: Goodbye ")
            break

        # Reset debug state for this fresh question
        STATE.reset()

        print("\n Thinking...\n")

        # Prepare initial state with messages and chat_history
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "chat_history": list(
                short_term_history
            ),  # Populate chat_history from conversation history
        }

        response = agent.invoke(initial_state)

        # Extract last message - ensure it's not None
        messages = response.get("messages", [])
        if not messages:
            print("[ERROR] No messages in response")
            continue

        final_message = messages[-1]
        if final_message is None:
            print("[ERROR] Final message is None")
            continue

        final_answer = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        # Update short-term history
        short_term_history.append(HumanMessage(content=user_input))
        short_term_history.append(AIMessage(content=final_answer))

        print(response)

        # Debug flow printing
        print(" DEBUG FLOW:")
        for msg in messages:
            if msg is None:
                print("   [SKIPPED] None message")
                continue
            if isinstance(msg, HumanMessage):
                print(f"   User: {msg.content}")
            elif isinstance(msg, AIMessage):
                print(f"   Model: {msg.content}")
            elif msg.__class__.__name__ == "ToolMessage":
                print(f"   {msg.name}: {msg.content}")

        print("\n----------------------------------")
        print(" Assistant:", final_answer)
        print("----------------------------------\n")


if __name__ == "__main__":
    run()
