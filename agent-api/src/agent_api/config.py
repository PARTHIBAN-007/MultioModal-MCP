from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file ="agent-api/.env",extra="ignore",env_file_encoding="utf-8")

    # GROQ_API_KEY:str = None
    GROQ_ROUTING_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_TOOL_USE_MODEL: str = "meta-llama/llama-4-maverick-17b-128e-instruct"
    GROQ_IMAGE_MODEL: str = "meta-llama/llama-4maverick-17b-128e-instruct"
    GROQ_GENERAL_MODEL: str = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # OPIK_API_KEY: str | None = Field(default=None,description="Opik API Key")
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT:str = Field(
        default="Agent-API",
        description="Agent API Tracking Service",
    )

    AGENT_MEMORY_SIZE: int = 20
    MCP_SERVER:str = "http://agent-mcp:8080/mcp"


lru_cache(maxsize=1)
def get_settings()->Settings:
    return Settings()