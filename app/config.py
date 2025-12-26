# -*- coding: utf-8 -*-
"""Configuration module responsible for loading environment variables and application settings."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

# Load environment variables from .env file if it exists
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

ENV_PATH = Path('.') / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# ======================================================
# Helpers
# ======================================================


def _as_bool(value: Optional[str], default: bool) -> bool:
    """Parse a truthy environment string into a boolean with fallback."""

    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ======================================================
# Email Configuration
# ======================================================
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS"), True)
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

# Ensure default sender is always defined
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME or "no-reply@elite-discounts.com"


class Config:
    """Application configuration sourced from environment variables with sensible defaults."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    RELAX_SECURITY_CONTROLS = _as_bool(os.getenv("RELAX_SECURITY_CONTROLS"), False)
    WTF_CSRF_ENABLED = _as_bool(os.getenv("WTF_CSRF_ENABLED"), not RELAX_SECURITY_CONTROLS)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost:5432/elite",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    MAIL_SERVER = MAIL_SERVER
    MAIL_PORT = MAIL_PORT
    MAIL_USE_TLS = MAIL_USE_TLS
    MAIL_USERNAME = MAIL_USERNAME
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_DEFAULT_SENDER = MAIL_DEFAULT_SENDER



try:
    database_name = make_url(Config.SQLALCHEMY_DATABASE_URI).database or "unknown"
except Exception:  # pragma: no cover - defensive logging
    database_name = "unknown"
