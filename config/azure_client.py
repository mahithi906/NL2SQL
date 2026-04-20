# Bridge between config and LLM Interactions
from openai import AzureOpenAI  # raw Azure OpenAI client
from langchain_openai import AzureChatOpenAI  # Lanchain wrapper for chat completions
from config.settings import load_azure_settings

settings = load_azure_settings()
# For direct API calls
azure_raw_client = AzureOpenAI(
    azure_endpoint=settings.endpoint,
    api_key=settings.api_key,
    api_version=settings.api_version,
)
# For our interactions
azure_llm = AzureChatOpenAI(
    azure_endpoint=settings.endpoint,
    api_key=settings.api_key,
    api_version=settings.api_version,
    deployment_name=settings.chat_deployment,
)
