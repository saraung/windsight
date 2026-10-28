from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "WindSight"
    app_env: str = "development"
    debug: bool = True

    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    elexon_timeout_seconds: float = Field(default=30.0, gt=0)
    elexon_max_retries: int = Field(default=2, ge=0, le=5)
    elexon_retry_backoff_seconds: float = Field(default=0.5, ge=0)

    cors_origins: str = "http://localhost:5173"
    data_cache_dir: str = "app/data"
    cache_ttl_hours: float = Field(default=24.0, gt=0)

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def data_cache_path(self) -> Path:
        path = Path(self.data_cache_dir)
        return path if path.is_absolute() else BACKEND_DIR / path


settings = Settings()
