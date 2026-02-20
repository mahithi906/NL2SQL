from pydantic import BaseModel
from typing import Optional


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
