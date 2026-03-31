"""Centralized configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    cohere_api_key: str

    # Qdrant (local)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # App settings
    max_file_size_mb: int = 500
    chunk_size: int = 600
    chunk_overlap: int = 80
    top_k_results: int = 5

    # Collection name
    qdrant_collection: str = "rag_documents"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
