from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    environment: Literal["development", "production"] = "development"
    jwt_secret: str = DEFAULT_JWT_SECRET
    db_backend: str = "memory"  # "memory" or "cosmos"
    cosmos_connection_string: str | None = None
    cosmos_database_name: str = "health_app"
    google_oauth_client_id: str | None = None
    apple_oauth_bundle_id: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    cors_allowed_origins: str = "http://localhost:8081,http://localhost:19006"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


def validate_production_settings(settings: Settings) -> None:
    """Raise if a production deployment is using unsafe dev defaults."""
    if settings.environment != "production":
        return
    if settings.jwt_secret == DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET must be set to a non-default value when ENVIRONMENT=production"
        )
    if settings.db_backend != "cosmos":
        raise RuntimeError(
            "DB_BACKEND must be 'cosmos' when ENVIRONMENT=production (in-memory backend "
            "loses all data on restart)"
        )
