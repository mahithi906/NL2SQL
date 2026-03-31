# langchain_project/app/routes.py

from fastapi import APIRouter
from app.schemas import NL2SQLRequest, NL2SQLResponse
from main import build_agent

router = APIRouter()


@router.post("/nl2sql", response_model=NL2SQLResponse)
async def nl2sql_api(payload: NL2SQLRequest):

    # Build a fresh agent instance per request so API calls do not share conversation memory
    agent = build_agent([])

    # ✅ Send user question to LangGraph agent
    result = agent.invoke({"messages": [{"role": "user", "content": payload.question}]})

    messages = result["messages"]

    # ✅ final model answer
    final_answer = messages[-1].content

    flow_trace = []
    sql = None
    rows = None
    row_count = None

    for msg in messages:
        mtype = msg.__class__.__name__

        if mtype == "HumanMessage":
            flow_trace.append(f"[USER] {msg.content}")

        elif mtype == "AIMessage":
            flow_trace.append(f"[MODEL] {msg.content}")

        elif mtype == "ToolMessage":
            flow_trace.append(f"[TOOL:{msg.name}] {msg.content}")

            try:
                # Attempt extraction of SQL/rows from ToolMessage
                data = eval(msg.content) if isinstance(msg.content, str) else None
                if isinstance(data, dict):
                    sql = data.get("sql", sql)
                    rows = data.get("rows", rows)
                    row_count = data.get("row_count", row_count)
            except:
                pass

    return NL2SQLResponse(
        answer=final_answer,
        sql=sql,
        rows=rows,
        row_count=row_count,
        flow=flow_trace,
    )
