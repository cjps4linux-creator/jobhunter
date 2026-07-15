from __future__ import annotations

import logging
import os as _os

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "JobHunter API"
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14


settings = Settings()

if not settings.secret_key:
    env = _os.getenv("APP_ENV", "development").lower()
    if env == "development":
        logger.warning(
            "SECURITY: SECRET_KEY not set; using insecure"
            " development fallback."
        )
        settings.secret_key = "dev-secret-key"
    else:
        raise RuntimeError(
            "SECRET_KEY must be set in non-development environments"
        )


def get_settings() -> Settings:
    return settings
