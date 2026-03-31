# langchain_project/app/schemas.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class NL2SQLRequest(BaseModel):
    question: str


class NL2SQLResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    flow: Optional[List[str]] = None
