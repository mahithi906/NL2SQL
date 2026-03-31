from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from config.settings import load_azure_settings

settings = load_azure_settings()

azure_raw_client = AzureOpenAI(
    azure_endpoint=settings.endpoint,
    api_key=settings.api_key,
    api_version=settings.api_version,
)

azure_llm = AzureChatOpenAI(
    azure_endpoint=settings.endpoint,
    api_key=settings.api_key,
    api_version=settings.api_version,
    deployment_name=settings.chat_deployment,
)
