# -*- coding: utf-8 -*-
"""Configuration module responsible for loading environment variables and application settings."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

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
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///elite.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    TIMEZONE = os.getenv("TIMEZONE", "UTC")


logger.info(
    "Configuration loaded: DB=%s, Redis=%s, Timezone=%s",
    Config.SQLALCHEMY_DATABASE_URI,
    Config.REDIS_URL,
    Config.TIMEZONE,
)
