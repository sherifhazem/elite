# Logging Guide

## 1. Goals
Provide a single, production-grade logging pipeline that is easy to reason about, produces structured JSON, and automatically captures request context.

## 2. Entry Points
- **Initialization:** `initialize_logging(app)` is called inside `app/__init__.py` during Flask app creation.
- **Retrieval:** Use `from app.logging.logger import get_logger` anywhere logging is needed. No other configuration is required.

## 3. Unified Logger Configuration
- All messages from the **root**, **flask.app**, and **werkzeug** loggers are routed through the same handler stack.
- Idempotent setup prevents duplicate handlers when the server reloads.
- Compatibility shim `app/core/central_logger.py` now defers to `app/logging/logger.py` to avoid legacy divergence.

## 4. Handler Strategy
- **Console Handler:** Colorized, human-readable output for local development.
- **JSON File Handler:** `logs/app.log.json`, rotated daily with a 4-day retention policy. Files are named `app.log.json.YYYY-MM-DD`.
- Both handlers share the same request-aware formatting pipeline so fields stay consistent across outputs.

## 5. Log Record Shape (JSON)
Each log line contains:
- `timestamp` (ISO 8601, UTC)
- `level`
- `message`
- `file`
- `function`
- `line`
- `request_id` (when available)
- `user_id` (when available)
- `path` and `method` (inside request context)

**Example:**
```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "level": "INFO",
  "message": "request_completed",
  "file": "central_middleware.py",
  "function": "end_request_logging",
  "line": 45,
  "request_id": "5f2c3f5a",
  "user_id": 42,
  "path": "/api/offers",
  "method": "GET"
}
```

## 6. Request and Tracking Integration
- `app/core/central_middleware.py` assigns a `request_id`, measures request duration, and emits lifecycle events through the centralized logger.
- Flask request context enrichment happens inside the formatter, so custom log statements automatically inherit path, method, request ID, and user ID when present.
- Tracking decorators or middleware should emit events via `get_logger()` to stay inside the centralized pipeline.

## 7. Rotation and Retention
- Daily rotation using `TimedRotatingFileHandler` keeps four days of history.
- Old archives are pruned automatically after the 4-day window.
- The log file is auto-created if it is missing; no manual setup is required.

## 8. Extending the Logger
- Add new metadata fields in `RequestAwareFormatter` to keep console and JSON outputs synchronized.
- Avoid attaching new handlers in modules; instead, adjust `_build_handlers()` when a new sink is required.
- Keep field names stable to avoid breaking downstream tooling that expects the current schema.

## 9. Accessing Logs
- Development tail: `tail -f logs/app.log.json`
- Review rotated files: `ls logs/app.log.json.*`
- Because logs are JSON-per-line, they can be streamed into tools like `jq` for quick inspection.

## 10. Troubleshooting
- Duplicate log lines usually mean a handler was added outside `initialize_logging`; ensure modules rely only on `get_logger()`.
- If Flask or Werkzeug messages are missing, confirm their loggers propagate to the root (set during initialization).
