# langchain_project/app/routes.py

from fastapi import APIRouter, HTTPException
from app.schemas import (
    NL2SQLRequest,
    NL2SQLResponse,
    SessionRequest,
    SessionResponse,
    HealthResponse,
)
from main import build_agent
from tools.state import STATE
from datetime import datetime
import uuid
import json

router = APIRouter()

# In-memory session storage (for single-instance deployment)
# For production, use Redis or a database
SESSIONS: dict = {}


# ============================================================
# HEALTH CHECK
# ============================================================
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
    )


# ============================================================
# SESSION MANAGEMENT
# ============================================================
@router.post("/session/create", response_model=SessionResponse)
async def create_session(payload: SessionRequest):
    """Create a new chat session."""
    session_id = payload.session_id or str(uuid.uuid4())

    SESSIONS[session_id] = {
        "session_id": session_id,
        "name": payload.name or f"Chat {session_id[:8]}",
        "created_at": datetime.utcnow().isoformat(),
        "history": [],  # Store full conversation history
        "last_sql": "",
        "last_rows": [],
        "last_error": "",
    }

    return SessionResponse(
        session_id=session_id,
        name=SESSIONS[session_id]["name"],
        created_at=SESSIONS[session_id]["created_at"],
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Retrieve session details."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    session = SESSIONS[session_id]
    return SessionResponse(
        session_id=session["session_id"],
        name=session["name"],
        created_at=session["created_at"],
    )


@router.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return [
        {
            "session_id": sid,
            "name": data["name"],
            "created_at": data["created_at"],
            "message_count": len(data["history"]),
        }
        for sid, data in SESSIONS.items()
    ]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    del SESSIONS[session_id]
    return {"status": "ok", "session_id": session_id}


# ============================================================
# NL2SQL PROCESSING
# ============================================================
@router.post("/nl2sql", response_model=NL2SQLResponse)
async def process_nl2sql(payload: NL2SQLRequest):
    """
    Process natural language question and return SQL + results.

    Flow:
    1. Build fresh agent with session history
    2. Invoke agent with user question
    3. Extract SQL, results, flow
    4. Store in session
    5. Return response
    """

    session_id = payload.session_id or str(uuid.uuid4())

    # Create session if doesn't exist
    if session_id not in SESSIONS:
        await create_session(SessionRequest(session_id=session_id))

    session = SESSIONS[session_id]
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Reset debug state for this fresh request
        STATE.reset()

        # Build agent with session conversation history
        agent = build_agent(session["history"])

        # Invoke agent
        response = agent.invoke({"messages": [{"role": "user", "content": question}]})

        # Extract messages
        messages = response.get("messages", [])

        # Extract final answer
        final_answer = ""
        if messages:
            final_answer = (
                messages[-1].content
                if hasattr(messages[-1], "content")
                else str(messages[-1])
            )

        # Extract SQL and results from tool messages
        sql = ""
        validated_sql = ""
        rows = []
        row_count = 0
        execution_error = ""
        flow_trace = []
        debug_info = None
        validator_info = None

        for msg in messages:
            mtype = msg.__class__.__name__

            if mtype == "HumanMessage":
                flow_trace.append(f"[USER] {msg.content}")

            elif mtype == "AIMessage":
                flow_trace.append(
                    f"[MODEL] {msg.content[:200]}"
                )  # Truncate for display

            elif mtype == "ToolMessage":
                tool_name = msg.name if hasattr(msg, "name") else "unknown"
                flow_trace.append(f"[{tool_name.upper()}]")

                # Parse tool output
                try:
                    if isinstance(msg.content, str):
                        # Try to parse as JSON first
                        try:
                            tool_output = json.loads(msg.content)
                        except:
                            tool_output = {"content": msg.content}

                        # Extract fields based on tool type
                        if tool_name == "schema_linker":
                            # Schema results are used by other tools, no direct extraction needed
                            pass
                        elif tool_name == "sql_synthesis":
                            sql = tool_output.get("sql", sql)
                        elif tool_name == "sql_validator":
                            validated_sql = tool_output.get(
                                "validated_sql", validated_sql
                            )
                            validator_error = tool_output.get("error", "")
                            if validator_error:
                                validator_info = {"error": validator_error}
                            else:
                                validator_info = {"validated": True}
                        elif tool_name == "sql_executor":
                            # Use the most recent SQL (validated if available, otherwise generated)
                            validated_sql = validated_sql or sql
                            rows = tool_output.get("rows", [])
                            row_count = tool_output.get("row_count", 0)
                            execution_error = tool_output.get("execution_error", "")
                        elif tool_name == "debug_agent":
                            debug_info = tool_output
                            if "corrected_sql" in tool_output:
                                sql = tool_output[
                                    "corrected_sql"
                                ]  # Update SQL with corrected version
                        elif tool_name == "answering_agent":
                            final_answer = tool_output.get("answer", final_answer)
                        elif tool_name == "general_answer":
                            final_answer = tool_output.get("answer", final_answer)
                except Exception:
                    pass

        # Update session history
        from langchain.messages import HumanMessage, AIMessage

        session["history"].append(HumanMessage(content=question))
        session["history"].append(AIMessage(content=final_answer))
        session["last_sql"] = validated_sql or sql
        session["last_rows"] = rows
        session["last_error"] = execution_error

        return NL2SQLResponse(
            answer=final_answer,
            sql=sql,
            validated_sql=validated_sql,
            rows=rows,
            row_count=row_count,
            execution_error=execution_error,
            flow=flow_trace,
            session_id=session_id,
            tokens_used=None,  # Add token counting if needed
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


@router.post("/nl2sql/chat")
async def chat_with_context(payload: NL2SQLRequest):
    """
    Alias for /nl2sql endpoint for frontend compatibility.
    """
    return await process_nl2sql(payload)
