from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Chip Tracker"
    database_url: str = "postgresql+asyncpg://chipping:chipping@localhost:5432/chipping"
    cors_origins: str = "http://localhost:5173,http://localhost:8000"
    static_dir: str | None = None
    app_git_sha: str | None = None
    app_build_version: str | None = None
    design_version: str = "v1-dashboard-polish"
    owner_pin: str | None = None
    owner_password: str | None = None
    jwt_secret: str | None = None
    session_days: int = 30
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def owner_credentials_configured(self) -> bool:
        return bool(self.owner_pin or self.owner_password)

    @property
    def auth_configured(self) -> bool:
        return bool(self.jwt_secret and self.owner_credentials_configured)


@lru_cache
def get_settings() -> Settings:
    return Settings()
