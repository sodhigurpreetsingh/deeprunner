from pydantic_settings import BaseSettings
from typing import List, Literal, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ===== Application Settings =====
    APP_NAME: str = "Document Search Service"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Distributed Document Search Service with Multi-Tenancy"
    DEBUG: bool = True

    # ===== Server Settings =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ===== CORS Settings =====
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ===== API Settings =====
    API_V1_PREFIX: str = "/api/v1"

    # ===== Environment Selection =====
    APP_ENV: Literal["dev", "prod"] = "dev"

    # ===== PostgreSQL Database Settings =====
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "docsearch"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    # ===== Elasticsearch Settings =====
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_SCHEME: str = "http"
    ELASTICSEARCH_INDEX_PREFIX: str = "documents"

    # ===== Redis Settings =====
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # ===== RabbitMQ Settings =====
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    # ===== Rate Limiting Settings =====
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: str = "100/minute"  # Default rate limit per tenant

    # ===== Search Settings =====
    MAX_SEARCH_RESULTS: int = 100
    SEARCH_TIMEOUT_SECONDS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def postgres_url(self) -> str:
        """PostgreSQL connection URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def postgres_async_url(self) -> str:
        """PostgreSQL async connection URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        """Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def elasticsearch_url(self) -> str:
        """Elasticsearch connection URL"""
        return f"{self.ELASTICSEARCH_SCHEME}://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"

    @property
    def rabbitmq_url(self) -> str:
        """RabbitMQ connection URL"""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
