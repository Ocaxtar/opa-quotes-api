"""Configuration module for opa-quotes-api."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "opa-quotes-api"
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+asyncpg://opa:opa_password@localhost:5432/quotes"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"

    # Monitoring
    prometheus_port: int = 9090

    # Authentication
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    environment: str = "development"
    cors_origins: list[str] = ["*"]

    # Circuit Breaker
    circuit_breaker_redis_fail_max: int = 5
    circuit_breaker_redis_timeout: int = 30
    circuit_breaker_db_fail_max: int = 3
    circuit_breaker_db_timeout: int = 60

    # Rate Limiting
    rate_limit_default: str = "100/minute"
    rate_limit_history: str = "20/minute"
    rate_limit_batch: str = "50/minute"

    @property
    def effective_cors_origins(self) -> list[str]:
        """Return CORS origins based on environment."""
        if self.environment == "production":
            return [
                "https://opa-dashboard.production.com",
                "https://app.opa-machine.com"
            ]
        elif self.environment == "staging":
            return ["https://opa-dashboard.staging.com"]
        else:  # development/integration
            return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
