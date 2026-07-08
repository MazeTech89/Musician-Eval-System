"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Musician Evaluation API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Server
    host: str = "0.0.0.0"  # noqa: S104 - Intentional for Docker/container deployment
    port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Database
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/musician_eval"

    # Security (MUST be set in production via environment variables)
    secret_key: str = "dev-secret-key-change-in-production"  # noqa: S105
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    rsa_private_key: str = ""
    rsa_public_key: str = ""

    # AWS S3 Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""  # Set from environment in production
    aws_secret_access_key: str = ""  # Set from environment in production
    s3_bucket_name: str = "musician-eval-uploads"  # Will be prefixed with environment
    s3_max_file_size_mb: int = 50  # Max 50MB audio files
    s3_allowed_audio_formats: list[str] = ["mp3", "wav", "flac", "m4a", "aac"]
    s3_signed_url_expiry_seconds: int = 3600  # 1 hour

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"

    @property
    def s3_bucket_name_with_env(self) -> str:
        """Return S3 bucket name with environment prefix."""
        return f"{self.environment}-{self.s3_bucket_name}"

    def get_s3_config(self) -> dict:
        """Get AWS S3 configuration for boto3."""
        return {
            "region_name": self.aws_region,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
        }


settings = Settings()
