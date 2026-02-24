from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class NL2SQLRequest(BaseModel):
    question: str
    options: Optional[Dict[str, Any]] = None


class NL2SQLResponse(BaseModel):
    answer: Optional[str] = None
    sql: Optional[str] = None
    result: Optional[List[Dict[str, Any]]] = None
    retries: int = 0
    error: Optional[str] = None
