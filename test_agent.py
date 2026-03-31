"""Testing the agent"""

from langchain.agents import create_agent
from config.azure_client import azure_llm

from tools.general_answers import general_answer
from tools.schema_linker import schema_linker
from tools.sql_synthesis import sql_synthesis
from tools.validator_guard import sql_validator
from tools.sql_executor import sql_executor
from tools.debug import debug_agent
from tools.answer import answering_agent

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
    system_prompt=(
        "You are an expert NL2SQL analytics assistant.\n"
        "Use the tools to answer questions about the database."
    ),
)

question = "What is the color of product CN-6137?"
print(f"Question: {question}")
print("-" * 60)

response = agent.invoke({"messages": [{"role": "user", "content": question}]})

print("Done!")
