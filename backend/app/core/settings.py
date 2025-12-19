from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEXICON_", env_file=".env", extra="ignore")

    # Comma-separated list of allowed origins for CORS
    cors_origins: str = "http://localhost:5173"

    # API base path versioning
    api_prefix: str = "/api/v1"

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
