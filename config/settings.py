import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AzureSettings:
    endpoint: str
    api_key: str
    chat_deployment: str
    embedding_deployment: str
    api_version: str


def load_azure_settings() -> AzureSettings:
    """
    Loads Azure OpenAI settings from .env.
    Ensures endpoint is ONLY base URL (no /openai/, no /deployments/...).
    """
    endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or ""
    chat_deployment = os.getenv("AZURE_CHAT_DEPLOYMENT") or ""
    embedding_deployment = os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT") or ""
    api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-08-01-preview"

    if not endpoint or not api_key or not chat_deployment:
        raise RuntimeError(
            "Missing Azure OpenAI configuration. "
            "Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_CHAT_DEPLOYMENT"
        )

    return AzureSettings(
        endpoint=endpoint,
        api_key=api_key,
        chat_deployment=chat_deployment,
        embedding_deployment=embedding_deployment,
        api_version=api_version,
    )
