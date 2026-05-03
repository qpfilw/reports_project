from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Enterprise Reporting Platform"
    app_version: str = "0.1.0"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:12345@localhost:5432/reporting_db",
        alias="DATABASE_URL",
    )

    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    jwt_secret_key: str = Field(
        default="change-me-access-secret",
        alias="JWT_SECRET_KEY",
    )
    jwt_refresh_secret_key: str = Field(
        default="change-me-refresh-secret",
        alias="JWT_REFRESH_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    storage_root: str = Field(default="storage", alias="STORAGE_ROOT")
    max_upload_size_mb: int = Field(default=25, alias="MAX_UPLOAD_SIZE_MB")

    processing_dispatch_mode: str = Field(default="sync", alias="PROCESSING_DISPATCH_MODE")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    celery_task_eager_propagates: bool = Field(default=False, alias="CELERY_TASK_EAGER_PROPAGATES")

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def storage_root_path(self) -> Path:
        root = Path(self.storage_root)
        return root if root.is_absolute() else self.project_root / root

@lru_cache
def get_settings() -> Settings:
    return Settings()
