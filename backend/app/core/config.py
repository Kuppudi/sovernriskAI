from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://sovereign:local_dev_only@localhost:5432/sovereign_risk"
    )
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    world_bank_base_url: str = "https://api.worldbank.org/v2"
    raw_data_dir: Path = Path("data/raw")


@lru_cache
def get_settings() -> Settings:
    return Settings()
