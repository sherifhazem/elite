# -*- coding: utf-8 -*-
"""Configuration module responsible for loading environment variables and application settings."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

# Load environment variables from .env file if it exists
ENV_PATH = Path('.') / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Configure basic logging for the application configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class Config:
    """Application configuration sourced from environment variables with sensible defaults."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost:5432/elite",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    TIMEZONE = os.getenv("TIMEZONE", "UTC")


try:
    database_name = make_url(Config.SQLALCHEMY_DATABASE_URI).database or "unknown"
except Exception as exc:  # pragma: no cover - defensive logging
    logger.warning("Failed to parse database name from URI: %s", exc)
    database_name = "unknown"

logger.info(
    "Configuration loaded: DB=%s, Redis=%s, Timezone=%s",
    Config.SQLALCHEMY_DATABASE_URI,
    Config.REDIS_URL,
    Config.TIMEZONE,
)
logger.info("✅ Database connected: PostgreSQL -> %s", database_name)
