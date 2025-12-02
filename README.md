# ELITE Platform

## Overview
ELITE is a modular Flask platform with centralized observability baked in. The logging system now auto-captures every request and response, correlation identifiers, breadcrumbs, timing, and validation details with zero per-route code.

## Global Logging & Tracking
- **Initialization:** `initialize_logging(app)` + `register_logging_middleware(app)` are wired inside `app/__init__.py`; no manual imports.
- **Coverage:** All routes and services inherit the same pipeline—request/response capture, correlation headers, masking, validation snapshots, and timing metrics.
- **Handlers:**
  - Colorized console output for local debugging.
  - JSON file output at `logs/app.log.json` rotated nightly with 4-day retention.
- **Idempotent:** Middleware and handler registration are guarded to avoid duplicates on reloads.

## Architecture (ASCII)
```
[Client] -> [Flask app]
    -> initialize_logging
    -> register_logging_middleware
         |- before_request: IDs + incoming payload capture
         |- route/service: breadcrumbs (+ optional @trace_execution)
         |- after_request: response capture + validation analysis + timing
         |- error_handler: structured exception snapshot
    -> RequestAwareFormatter -> console + JSON sinks
```

## Capture Matrix
- **Incoming:** method, full path, query params, form data, JSON payload, non-sensitive headers, file names/extensions → `request.meta.incoming_payload`.
- **Outgoing:** status code, JSON body (if JSON), error payloads, redirect target, response size → `request.meta.outgoing_payload`.
- **Correlation:** `request_id`, `trace_id`, optional `parent_id`, and `user_id` when authenticated (echoed in response headers).
- **Breadcrumbs:** stored in `request.meta.trace` from middleware checkpoints, validation detection, error handlers, and optional `@trace_execution` service decorators.
- **Timing:** `total_ms`, `middleware_ms`, `route_ms`, `service_ms` emitted in every log entry.

## Masking & Safety
Sensitive keys (`password`, `token`, `authorization`, `cookie`, `csrf_token`) are masked or removed across payloads and headers. File logging keeps only filenames and extensions; payload snapshots are sanitized before persistence.

## Validation & Error Logging
- 400/422 responses automatically emit a `validation_failed` block with missing/invalid fields, allowed values, received values, and a diagnostic message.
- Exceptions emit structured records with type, message, traceback, source file/function/line, payload snapshot, breadcrumbs, correlation IDs, and elapsed time to failure.

## Output Format
Each request generates one JSON log entry containing timestamp, level, correlation IDs, path/method, incoming/outgoing payloads, breadcrumbs, validation snapshot, timing block, response status, and file/function/line metadata.

## Further Reading
- `doc/LOGGING.md` — detailed pipeline, examples, and troubleshooting.
- `doc/TRACKING.md` — correlation IDs, breadcrumbs, validation, and timing behavior.
- `doc/OBSERVABILITY.md` — broader observability overview for the platform.
