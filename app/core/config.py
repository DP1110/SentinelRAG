from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List


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
    # High-concurrency Connection Pool Settings (for 1,000+ concurrent users)
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 100
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Redis Distributed Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_REDIS: bool = True
    
    # Response Cache (Permission-Isolated Semantic Cache)
    ENABLE_RESPONSE_CACHE: bool = True
    RESPONSE_CACHE_TTL_SECONDS: int = 300  # 5 minutes
    
    # Distributed Rate Limiter
    ENABLE_RATE_LIMITER: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120  # requests per minute per identity
    
    # Async Background Audit Logging
    ASYNC_AUDIT_LOGGING: bool = True
    
    # Observability & Metrics
    ENABLE_METRICS: bool = True
    
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
