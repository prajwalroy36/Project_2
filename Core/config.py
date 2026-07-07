from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from .env and can be overridden
    by environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------
    # Application
    # -------------------------------------------------

    APP_NAME: str = "Order Operations Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # -------------------------------------------------
    # Database
    # -------------------------------------------------

    DATABASE_URL: str

    # -------------------------------------------------
    # Shopify
    # -------------------------------------------------

    SHOPIFY_ACCESS_TOKEN: str = ""
    SHOPIFY_WEBHOOK_SECRET: str = ""

    # -------------------------------------------------
    # Warehouse
    # -------------------------------------------------

    SFTP_HOST: str
    SFTP_PORT: int = 22
    SFTP_USER: str
    SFTP_PASS: str

    SFTP_UPLOAD_DIR: str = "/incoming"
    SFTP_TRACKING_DIR: str = "/tracking"

    # -------------------------------------------------
    # Discord
    # -------------------------------------------------

    DISCORD_WEBHOOK_URL: str = ""

    # -------------------------------------------------
    # Processing
    # -------------------------------------------------

    MAX_RETRIES: int = Field(default=3, ge=0)

    WORKER_SLEEP_SECONDS: int = Field(
        default=5,
        ge=1,
    )

    # -------------------------------------------------
    # Logging
    # -------------------------------------------------

    # -------------------------------------------------
    # Frontend Dashboard
    # -------------------------------------------------
    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_API_KEY: str = "super_secret_dev_key_123"

    

    LOG_LEVEL: Literal[
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    ] = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()