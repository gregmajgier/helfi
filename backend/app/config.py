from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str = "dev-secret-change-me"
    db_backend: str = "memory"  # "memory" or "cosmos"
    cosmos_connection_string: str | None = None
    cosmos_database_name: str = "health_app"
    google_oauth_client_id: str | None = None
    apple_oauth_bundle_id: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
