"""Configuration module for opa-quotes-api."""
from functools import lru_cache

# OPA-325: Try to load DB config from opa-infrastructure-state/state.yaml
_default_db_url = "postgresql+asyncpg://opa_user:opa_password@localhost:5433/opa_quotes"

try:
    infra_state_path = Path(__file__).parent.parent.parent / 'opa-infrastructure-state'
    if infra_state_path.exists():
        sys.path.insert(0, str(infra_state_path))
        from config_loader import get_db_config
        _config = get_db_config('quotes')
        _default_db_url = f"postgresql+asyncpg://{_config['user']}:{_config['password']}@{_config['host']}:{_config['port']}/{_config['database']}"
        print(f"✓ OPA-325: Loaded DB config from state.yaml: port={_config['port']}")
except Exception:
    pass  # Fallback to default


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
    database_url: str = _default_db_url
    # Authentication
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    environment: str = "development"
    cors_origins: list[str] = ["*"]

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
