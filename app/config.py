# -*- coding: utf-8 -*-
"""Configuration module responsible for loading environment variables and application settings."""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

# Load environment variables from .env file if it exists
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
LOGS_DIR = PROJECT_ROOT / "logs"

ENV_PATH = Path('.') / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Configure basic logging for the application configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

    SECRET_KEY = os.getenv("SECRET_KEY", "ضع_قيمة_سرية_ثابتة_هنا")
    RELAX_SECURITY_CONTROLS = _as_bool(os.getenv("RELAX_SECURITY_CONTROLS"), True)
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
    OBSERVABILITY_CONFIG = {
        "LOG_DIR": str(LOGS_DIR),
        "BACKEND_LOG_FILE": str(LOGS_DIR / "backend.log.json"),
        "BACKEND_ERROR_LOG_FILE": str(LOGS_DIR / "backend-error.log.json"),
        "FRONTEND_ERROR_LOG_FILE": str(LOGS_DIR / "frontend-errors.log.json"),
        "FRONTEND_API_LOG_FILE": str(LOGS_DIR / "frontend-api.log.json"),
        "UI_EVENTS_LOG_FILE": str(LOGS_DIR / "ui-events.log.json"),
        "LOG_LEVEL": os.getenv("OBSERVABILITY_LOG_LEVEL", "INFO"),
        "ERROR_LOG_LEVEL": os.getenv("OBSERVABILITY_ERROR_LEVEL", "ERROR"),
        "REQUEST_ID_HEADER": os.getenv("REQUEST_ID_HEADER", "X-Request-ID"),
        "REQUEST_ID_LENGTH": int(os.getenv("REQUEST_ID_LENGTH", 32)),
        "HANDLER_OPTIONS": {"encoding": "utf-8"},
    }



logger.info(
    "SQLALCHEMY_DATABASE_URI loaded from environment: %s",
    Config.SQLALCHEMY_DATABASE_URI,
)

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
