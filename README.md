# ELITE Platform

## Overview
The ELITE application is a modular Flask platform built around a centralized infrastructure for security, observability, and modular business domains. This README highlights the logging and observability model introduced in this iteration so contributors can reason about runtime behavior quickly.

## Centralized Logging
- **Module:** `app/logging/logger.py`
- **Activation:** Automatically initialized inside `app/__init__.py` when the Flask app is created.
- **Coverage:** Unifies the **root**, **flask.app**, and **werkzeug** loggers so every message flows through the same handlers.
- **Handlers:**
  - Console handler with colored human-readable output for development.
  - Timed rotating JSON file handler at `logs/app.log.json` with a 4-day retention window.
- **Format:** JSON with `timestamp`, `level`, `message`, `file`, `function`, `line`, `request_id` (when available), `user_id` (when known), and request `path`/`method` when a Flask request context exists.
- **Idempotency:** Handler attachment is guarded so reloading the app does not duplicate handlers.

## Log Rotation and Access
- **Location:** `logs/app.log.json` (auto-created on startup if missing).
- **Rotation:** Daily rotation via `TimedRotatingFileHandler` with filenames like `app.log.json.2025-01-01`; only the last **4** days are retained.
- **Viewing Logs:**
  - Tail JSON logs during development: `tail -f logs/app.log.json`
  - Inspect rotated archives: `ls logs/app.log.json.*`

## Tracking and Request Context
- Request lifecycle hooks in `app/core/central_middleware.py` enrich log entries with `request_id`, HTTP method, and path. Errors also capture duration and bubble through the centralized logger.
- User context is automatically injected into logs when `g.current_user` or Flask-Login state is available.

## Extending the Logger
- Use `from app.logging.logger import get_logger` to obtain a logger; no other configuration is required.
- Keep formatting consistent by allowing the centralized formatter to run; do not attach custom handlers in modules.
- To add new metadata, extend `RequestAwareFormatter` in `app/logging/logger.py` so both console and JSON outputs stay aligned.

## Documentation
Further logging guidance lives in:
- `doc/LOGGING.md` — deep dive into the logging pipeline and examples.
- `config/logging_config.md` — operational notes and configuration knobs.
- `doc/OBSERVABILITY.md` — overview of the observability layer.
