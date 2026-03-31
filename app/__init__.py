# langchain_project/app/__init__.py

from fastapi import FastAPI
from app.routes import router as api_router


def create_app():
    app = FastAPI(
        title="NL2SQL Agent API",
        description="Natural Language → SQL agent using LangGraph + Azure OpenAI",
        version="1.0.0",
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
