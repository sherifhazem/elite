# Logging Configuration Notes

## Central Module
- Implementation lives in `app/logging/logger.py`.
- Initialization occurs via `initialize_logging(app)` inside `app/__init__.py`.

## Handlers
- **Console:** Colorized output for developers.
- **File:** `logs/app.log.json` using `TimedRotatingFileHandler` with daily rotation and 4-day retention.

## Format
- Structured JSON including timestamp, level, message, file, function, line, request_id, user_id, path, and method when a request context exists.

## Rotation Policy
- Rotation time: midnight (UTC).
- Retention: keep 4 historical files named `app.log.json.YYYY-MM-DD`.
- The base log file is auto-created; no manual provisioning required.

## Usage Rules
- Retrieve loggers with `get_logger` from the centralized module.
- Do not attach ad-hoc handlers or formatters in modules or blueprints.
- Tracking middleware (`app/core/central_middleware.py`) and any decorators must emit through the same logger to maintain consistency.

## Extensibility
- Add new sinks by extending `_build_handlers()` while keeping both handlers aligned with the shared formatter pipeline.
- Add new contextual fields inside `RequestAwareFormatter` so JSON and console outputs remain in sync.
