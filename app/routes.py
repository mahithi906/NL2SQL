from fastapi import APIRouter, HTTPException
from typing import List
from .schemas import Item, ItemCreate, NL2SQLRequest, NL2SQLResponse
from .graph import nl2sql_graph, MAX_RETRIES

router = APIRouter(prefix="/api")

_items_db = {}
_next_id = 1


@router.get("/items", response_model=List[Item])
def list_items():
    return list(_items_db.values())


@router.post("/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate):
    global _next_id
    item = Item(id=_next_id, name=payload.name, description=payload.description)
    _items_db[_next_id] = item
    _next_id += 1
    return item


@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = _items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/nl2sql/query", response_model=NL2SQLResponse)
def nl2sql_query(payload: NL2SQLRequest):
    """Run a natural-language question through the LangGraph NL2SQL pipeline."""
    initial_state = {
        "question": payload.question,
        "schema_context": None,
        "sql": None,
        "validation_error": None,
        "result": None,
        "execution_error": None,
        "answer": None,
        "retries": 0,
    }
    final_state = nl2sql_graph.invoke(initial_state)
    if final_state.get("execution_error") and final_state.get("retries", 0) >= MAX_RETRIES:
        return NL2SQLResponse(
            error=final_state["execution_error"],
            retries=final_state.get("retries", 0),
        )
    return NL2SQLResponse(
        answer=final_state.get("answer"),
        sql=final_state.get("sql"),
        result=final_state.get("result"),
        retries=final_state.get("retries", 0),
    )
