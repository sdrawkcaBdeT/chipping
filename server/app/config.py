from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Chip Tracker"
    database_url: str = "postgresql+asyncpg://chipping:chipping@localhost:5432/chipping"
    cors_origins: str = "http://localhost:5173,http://localhost:8000"
    static_dir: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
