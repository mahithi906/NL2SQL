import os
from dotenv import load_dotenv
from typing import Any, List
from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState, AgentMiddleware
from langchain.messages import HumanMessage, AIMessage
from config.azure_client import azure_llm
from config.settings import load_azure_settings
from tools.general_answers import general_answer
from tools.schema_linker import schema_linker
from tools.sql_synthesis import sql_synthesis
from tools.validator_guard import sql_validator
from tools.sql_executor import sql_executor
from tools.debug import debug_agent
from tools.answer import answering_agent

load_dotenv()
settings = load_azure_settings()


short_term_history = []


class CustomState(AgentState):
    chat_history: List[Any]


class MemoryAwareMiddleware(AgentMiddleware):
    state_schema = CustomState

    def __init__(self, hist_ref):
        self.hist_ref = hist_ref

    def wrap_tool_call(self, request, handler):
        tool_name = request.tool.name if request.tool else None

        tools_requiring_context = {
            "general_answer",
            "schema_linker",
            "sql_synthesis",
            "debug_agent",
            "answering_agent",
        }

        if tool_name in tools_requiring_context:
            tool_call = request.tool_call
            args = dict(tool_call.get("args", {}) or {})
            args["short_term_history"] = self.hist_ref[:]  # pass copy
            return handler(request.override(tool_call={**tool_call, "args": args}))

        return handler(request)


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
            "You are an expert NL2SQL analytics assistant.\n"
            "Maintain a short-term conversational memory to provide context for multi-turn interactions.\n"
            "You can:\n"
            "- Answer general questions about the database\n"
            "- Identify relevant tables & columns\n"
            "- Generate SQL queries\n"
            "- Validate SQL\n"
            "- Execute SQL\n"
            "- Debug SQL when needed\n"
            "- Summarize results in natural language\n\n"
            "Use the tools appropriately depending on the user's question.\n"
            "If SQL is needed, follow this pipeline:\n"
            "  schema_linker -> sql_synthesis -> sql_validator -> sql_executor -> answering_agent\n"
            "For errors during execution, use debug_agent to repair SQL.\n"
            "Always return a final natural-language answer to the user.\n"
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

        print("\n Thinking...\n")

        # Invoke new LangChain v1 agent
        response = agent.invoke({"messages": [{"role": "user", "content": user_input}]})

        # Extract last message
        final_answer = response["messages"][-1].content

        short_term_history.append(HumanMessage(content=user_input))
        short_term_history.append(AIMessage(content=final_answer))
        print(response)

        # Debug flow printing
        print(" DEBUG FLOW:")
        for msg in response["messages"]:
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
