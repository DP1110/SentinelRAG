from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "SentinelRAG"
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = "sentinelrag-development-secret-key-32-chars-min"
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./sentinelrag.db",
        description="Database connection string (PostgreSQL with pgvector in production, SQLite for local/testing)"
    )
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Models
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Retrieval defaults
    DEFAULT_TOP_K: int = 8
    DEFAULT_RERANK_TOP_K: int = 50
    RRF_K: int = 60
    
    # Authorization & Security
    ACL_CACHE_TTL_SECONDS: int = 60
    FAIL_CLOSED_ON_ACL_ERROR: bool = True
    MAX_AGENT_STEPS: int = 5
    
    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None


settings = Settings()
