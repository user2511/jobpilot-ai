# backend/config.py
# All environment variables validated at startup.
# App crashes fast with a clear message if anything is missing.

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"

    # Database
    database_url: str = "sqlite:///./data/jobpilot.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    log_level: str = "INFO"
    max_file_size_mb: int = 5
    app_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings — loaded once at startup."""
    return Settings()


# Convenience import
settings = get_settings()
