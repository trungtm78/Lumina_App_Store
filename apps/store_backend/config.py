"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://lumina:lumina_dev@localhost:5432/lumina_store"
    database_url_sync: str = "postgresql://lumina:lumina_dev@localhost:5432/lumina_store"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300  # 5 min

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "lumina_minio"
    minio_secret_key: str = "lumina_minio_dev"
    minio_bucket: str = "lumina-apps"
    minio_secure: bool = False

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h

    # Storage
    lumina_apps_dir: str = "./LuminaApps"  # Central ZIP storage for approved apps

    # Limits
    max_zip_size: int = 50 * 1024 * 1024  # 50MB
    max_py_file_size: int = 5 * 1024 * 1024  # 5MB

    model_config = {"env_prefix": "LUMINA_"}


settings = Settings()
