from fastapi import APIRouter, HTTPException
from typing import List
from .schemas import Item, ItemCreate

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
