"""LangGraph skeleton for the NL2SQL pipeline.

Pipeline flow:
  schema_linker → sql_synthesizer → validator → executor
                                                    ↓
                               (rows returned) answer_generator → END
                               (empty / error) debug_agent → schema_linker (retry)
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, StateGraph


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class NL2SQLState(TypedDict):
    """Shared state passed between every node in the graph."""

    question: str
    schema_context: Optional[str]
    sql: Optional[str]
    validation_error: Optional[str]
    result: Optional[List[Dict[str, Any]]]
    execution_error: Optional[str]
    answer: Optional[str]
    retries: int


# ---------------------------------------------------------------------------
# Nodes  (stub implementations – replace with real logic)
# ---------------------------------------------------------------------------

def schema_linker(state: NL2SQLState) -> NL2SQLState:
    """Retrieve relevant schema / metadata for the user question."""
    return {**state, "schema_context": "<schema placeholder>"}


def sql_synthesizer(state: NL2SQLState) -> NL2SQLState:
    """Generate SQL from the question and schema context."""
    return {**state, "sql": "SELECT 1 -- placeholder", "validation_error": None}


def validator(state: NL2SQLState) -> NL2SQLState:
    """Validate the generated SQL (SELECT-only, schema-aware)."""
    sql = state.get("sql", "")
    if not sql.strip().upper().startswith("SELECT"):
        return {**state, "validation_error": "Only SELECT statements are allowed."}
    return {**state, "validation_error": None}


def executor(state: NL2SQLState) -> NL2SQLState:
    """Execute the validated SQL against the database."""
    if state.get("validation_error"):
        return {**state, "result": None, "execution_error": state["validation_error"]}
    # Stub: replace with real DB execution
    return {**state, "result": [], "execution_error": None}


def debug_agent(state: NL2SQLState) -> NL2SQLState:
    """Attempt to auto-repair the SQL when execution fails or returns empty."""
    return {**state, "retries": state.get("retries", 0) + 1, "sql": None}


def answer_generator(state: NL2SQLState) -> NL2SQLState:
    """Produce a human-friendly answer from the query result."""
    rows = state.get("result") or []
    answer = f"Query returned {len(rows)} row(s)."
    return {**state, "answer": answer}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

MAX_RETRIES = 3


def route_after_executor(
    state: NL2SQLState,
) -> Literal["answer_generator", "debug_agent", END]:
    """Route based on the execution outcome."""
    if state.get("execution_error"):
        if state.get("retries", 0) >= MAX_RETRIES:
            return END
        return "debug_agent"
    rows = state.get("result")
    if rows is None or len(rows) == 0:
        if state.get("retries", 0) >= MAX_RETRIES:
            return "answer_generator"
        return "debug_agent"
    return "answer_generator"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the NL2SQL LangGraph."""
    graph = StateGraph(NL2SQLState)

    graph.add_node("schema_linker", schema_linker)
    graph.add_node("sql_synthesizer", sql_synthesizer)
    graph.add_node("validator", validator)
    graph.add_node("executor", executor)
    graph.add_node("debug_agent", debug_agent)
    graph.add_node("answer_generator", answer_generator)

    graph.set_entry_point("schema_linker")

    graph.add_edge("schema_linker", "sql_synthesizer")
    graph.add_edge("sql_synthesizer", "validator")
    graph.add_edge("validator", "executor")

    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "answer_generator": "answer_generator",
            "debug_agent": "debug_agent",
            END: END,
        },
    )

    graph.add_edge("debug_agent", "schema_linker")
    graph.add_edge("answer_generator", END)

    return graph.compile()


nl2sql_graph = build_graph()
