from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WindSight"
    app_env: str = "development"
    debug: bool = True

    elexon_base_url: str = (
        "https://data.elexon.co.uk/bmrs/api/v1"
    )
    cors_origins: str = "http://localhost:5173"
    data_cache_dir: str = "app/data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()