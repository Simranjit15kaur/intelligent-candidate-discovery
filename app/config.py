# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Intelligent Candidate Discovery"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2-preview"

    # Pipeline tuning
    RETRIEVAL_TOP_K: int = 200        # Stage 1 — how many candidates pass to Stage 2
    EXPLANATION_TOP_K: int = 50       # Stage 4/5 — how many candidates get LLM explanation
    BM25_WEIGHT: float = 0.4          # RRF fusion weight for BM25
    EMBEDDING_WEIGHT: float = 0.6     # RRF fusion weight for semantic search

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# single instance imported everywhere
settings = Settings()