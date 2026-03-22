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

    jwt_secret_key: str = Field(
        default="AHBPsz1CpB39lI4ih1i5lFUzwxLIDtCBMGc8eb9RQcPv5hPTgxSE8uLkUAp92omD",
        alias="JWT_SECRET_KEY",
    )
    jwt_refresh_secret_key: str = Field(
        default="Mcu4v5SArhV8KhXbxY_cHmTt2F8gGi81BYK3EIswuF6UqrCNcJBVfpxwUBjFgxVK",
        alias="JWT_REFRESH_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    storage_root: str = Field(default="storage", alias="STORAGE_ROOT")
    max_upload_size_mb: int = Field(default=25, alias="MAX_UPLOAD_SIZE_MB")

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
    
    admin_bootstrap_enabled: bool = Field(default=False, alias="ADMIN_BOOTSTRAP_ENABLED")
    admin_bootstrap_email: str | None = Field(default=None, alias="ADMIN_BOOTSTRAP_EMAIL")
    admin_bootstrap_password: str | None = Field(default=None, alias="ADMIN_BOOTSTRAP_PASSWORD")
    admin_bootstrap_full_name: str | None = Field(default=None, alias="ADMIN_BOOTSTRAP_FULL_NAME")
    admin_bootstrap_position: str | None = Field(default=None, alias="ADMIN_BOOTSTRAP_POSITION")
    admin_bootstrap_department: str | None = Field(default=None, alias="ADMIN_BOOTSTRAP_DEPARTMENT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
