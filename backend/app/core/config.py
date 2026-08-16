"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Musician Evaluation API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104 - Intentional for container networking
    port: int = 8000

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/musician_eval"

    # Security
    secret_key: str = "your-secret-key-change-in-production"  # noqa: S105 - Default for dev, change in production
    secret_key_fallbacks: str = (
        ""  # comma-separated old secrets, still accepted during key rotation
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    require_email_verification: bool = False
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    security_alert_email: str | None = None
    login_lockout_max_attempts: int = 5
    login_lockout_minutes: int = 1
    password_reset_cooldown_seconds: int = 60
    # RSA keys for RS256 (should be set in production environment)
    # Currently unused: algorithm is HS256 and no code path signs/verifies with these keys.
    # Reserved for a future RS256 migration.
    rsa_private_key: str = ""
    rsa_public_key: str = ""
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True

    # Upload storage
    # Local disk upload storage is the default for development and tests. This matches
    # the Docker/dev configuration and keeps the app functional without requiring S3
    # credentials for everyday local work.
    use_local_upload_storage: bool = True
    local_upload_dir: str = "uploads"
    max_audio_upload_size_mb: int = 300
    s3_fallback_to_local: bool = (
        True  # if S3 isn't configured/reachable, save to local disk instead
    )

    # AWS S3
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_endpoint_url: str | None = None
    s3_allowed_audio_formats: list[str] = ["mp3", "wav", "m4a", "ogg", "flac"]
    s3_max_file_size_mb: int = 300
    s3_signed_url_expiry_seconds: int = 3600

    @property
    def s3_bucket_name_with_env(self) -> str:
        """Return the resolved S3 bucket name, including the environment prefix when needed."""
        bucket_name = self.s3_bucket_name or "musician-eval-uploads"
        env_name = (self.environment or "development").lower()
        if env_name in {"production", "prod", "staging"}:
            return bucket_name
        prefix = f"{env_name}-"
        if bucket_name.startswith(prefix):
            return bucket_name
        return f"{prefix}{bucket_name}"

    def get_s3_config(self) -> dict[str, str]:
        """Build boto3 S3 client config from the active settings."""
        config: dict[str, str] = {}
        if self.aws_region:
            config["region_name"] = self.aws_region
        if self.aws_access_key_id:
            config["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            config["aws_secret_access_key"] = self.aws_secret_access_key
        if self.s3_endpoint_url:
            config["endpoint_url"] = self.s3_endpoint_url
        return config


settings = Settings()
