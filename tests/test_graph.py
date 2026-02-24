from fastapi.testclient import TestClient
from main import app
from app.graph import (
    NL2SQLState,
    nl2sql_graph,
    schema_linker,
    sql_synthesizer,
    validator,
    executor,
    debug_agent,
    answer_generator,
    route_after_executor,
    MAX_RETRIES,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for individual nodes
# ---------------------------------------------------------------------------

def _base_state(**kwargs) -> NL2SQLState:
    return {
        "question": "test question",
        "schema_context": None,
        "sql": None,
        "validation_error": None,
        "result": None,
        "execution_error": None,
        "answer": None,
        "retries": 0,
        **kwargs,
    }


def test_schema_linker_adds_context():
    state = schema_linker(_base_state())
    assert state["schema_context"] is not None


def test_sql_synthesizer_adds_sql():
    state = sql_synthesizer(_base_state(schema_context="<schema>"))
    assert state["sql"] is not None
    assert state["validation_error"] is None


def test_validator_rejects_non_select():
    state = validator(_base_state(sql="DROP TABLE foo"))
    assert state["validation_error"] is not None


def test_validator_accepts_select():
    state = validator(_base_state(sql="SELECT 1"))
    assert state["validation_error"] is None


def test_executor_returns_result_on_valid_sql():
    state = executor(_base_state(sql="SELECT 1", validation_error=None))
    assert state["execution_error"] is None
    assert isinstance(state["result"], list)


def test_executor_propagates_validation_error():
    state = executor(_base_state(sql="DROP TABLE foo", validation_error="Only SELECT allowed."))
    assert state["execution_error"] is not None


def test_debug_agent_increments_retries():
    state = debug_agent(_base_state(retries=1))
    assert state["retries"] == 2


def test_answer_generator_formats_answer():
    state = answer_generator(_base_state(result=[{"col": "val"}]))
    assert "1" in state["answer"]


def test_answer_generator_with_empty_result():
    state = answer_generator(_base_state(result=[]))
    assert "0" in state["answer"]


def test_route_rows_returned_non_empty():
    """Ensure that a non-empty result set always routes to answer_generator."""
    for n_rows in (1, 5, 100):
        state = _base_state(result=[{"x": i} for i in range(n_rows)], execution_error=None)
        assert route_after_executor(state) == "answer_generator"


# ---------------------------------------------------------------------------
# Unit tests for routing
# ---------------------------------------------------------------------------

def test_route_rows_returned():
    state = _base_state(result=[{"col": "val"}], execution_error=None)
    assert route_after_executor(state) == "answer_generator"


def test_route_empty_result_under_max_retries():
    state = _base_state(result=[], execution_error=None, retries=0)
    assert route_after_executor(state) == "debug_agent"


def test_route_empty_result_at_max_retries():
    state = _base_state(result=[], execution_error=None, retries=MAX_RETRIES)
    assert route_after_executor(state) == "answer_generator"


def test_route_execution_error_under_max_retries():
    state = _base_state(result=None, execution_error="DB error", retries=0)
    assert route_after_executor(state) == "debug_agent"


def test_route_execution_error_at_max_retries():
    from langgraph.graph import END
    state = _base_state(result=None, execution_error="DB error", retries=MAX_RETRIES)
    assert route_after_executor(state) == END


# ---------------------------------------------------------------------------
# Integration test: full graph execution
# ---------------------------------------------------------------------------

def test_graph_returns_answer():
    result = nl2sql_graph.invoke({
        "question": "How many work orders exist?",
        "schema_context": None,
        "sql": None,
        "validation_error": None,
        "result": None,
        "execution_error": None,
        "answer": None,
        "retries": 0,
    })
    assert result.get("answer") is not None


# ---------------------------------------------------------------------------
# API endpoint test
# ---------------------------------------------------------------------------

def test_nl2sql_query_endpoint():
    resp = client.post("/api/nl2sql/query", json={"question": "Show total cost for January 2024"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
