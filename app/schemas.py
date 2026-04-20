# langchain_project/app/schemas.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class NL2SQLRequest(BaseModel):
    """Frontend request for NL2SQL processing."""

    question: str
    session_id: Optional[str] = None


class NL2SQLResponse(BaseModel):
    """Backend response with SQL, results, and execution flow."""

    answer: str
    sql: Optional[str] = None
    validated_sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    execution_error: Optional[str] = None
    flow: Optional[List[str]] = None
    session_id: Optional[str] = None
    tokens_used: Optional[int] = None
    debug_info: Optional[Dict[str, Any]] = None
    validator_info: Optional[Dict[str, Any]] = None


class SessionRequest(BaseModel):
    """Request to create or retrieve a session."""

    session_id: Optional[str] = None
    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Response containing session info."""

    session_id: str
    name: str
    created_at: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
