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
    host: str = "127.0.0.1"
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
    secret_key_fallbacks: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    require_email_verification: bool = False
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    security_alert_email: str | None = None
    # RSA keys for RS256 (should be set in production environment)
    rsa_private_key: str = ""
    rsa_public_key: str = ""
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True

    # Upload storage
    use_local_upload_storage: bool = False
    local_upload_dir: str = "uploads"
    max_audio_upload_size_mb: int = 300
    s3_fallback_to_local: bool = True

    # AWS S3
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_endpoint_url: str | None = None


settings = Settings()
