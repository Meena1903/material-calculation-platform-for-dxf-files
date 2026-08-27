from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "SkillBridge"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "skillbridge-poc-secret-key-change-in-prod"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite+aiosqlite:///./skillbridge.db"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    nvidia_chat_model: str = "meta/llama-3.1-8b-instruct"

    w_relevance: float = 0.40
    w_trust: float = 0.15
    w_authority: float = 0.15
    w_freshness: float = 0.15
    w_engagement: float = 0.15
    spam_penalty: float = 0.30

    cold_start_interactions: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
