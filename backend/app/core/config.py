"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Musician Evaluation API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"  # noqa: S104 - Intentional for Docker/container deployment
    port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/musician_eval"

    # Security
    secret_key: str = "your-secret-key-change-in-production"  # noqa: S105 - Default for dev, change in production
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # RSA keys for RS256 (should be set in production environment)
    rsa_private_key: str = ""
    rsa_public_key: str = ""


settings = Settings()
