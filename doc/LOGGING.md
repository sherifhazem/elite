# Logging Guide

## Overview
A single, centralized logging pipeline captures every request/response pair, errors, timings, and correlation metadata without any per-route code. Initialization is automatic through `initialize_logging(app)` and the global middleware stack.

## Architecture (ASCII)
```
[Flask WSGI]
    |-> initialize_logging(app)
    |-> register_logging_middleware(app)
            |-> before_request: build context, request_id/trace_id, incoming payload capture
            |-> route/blueprint execution (breadcrumbs + optional @trace_execution)
            |-> after_request: response capture, validation probe, timing synthesis
            |-> errorhandler: structured exception snapshot + breadcrumb
            |-> RequestAwareFormatter -> JSON line (file + console, rotated daily)
```

## What gets captured (automatic)
- **Incoming**: method, full path, query params, form data, JSON body (when available), headers (sensitive headers dropped), and file names/extensions → `request.meta.incoming_payload`.
- **Outgoing**: status code, JSON body (if JSON), error payload (status ≥ 400), redirect target, response size → `request.meta.outgoing_payload`.
- **Correlation**: `request_id`, `trace_id`, optional `parent_id`, resolved `user_id` (if authenticated) → injected into headers and logs.
- **Tracing**: `request.meta.trace` accumulates breadcrumbs from middleware checkpoints, error handlers, and any optional `@trace_execution` service decorators.
- **Validation**: client errors (400 / 422) automatically log missing fields, invalid fields, allowed values, received values, and a diagnostic message.

## Breadcrumbs & execution tracing
Breadcrumb entries carry file/function/line plus a human message. Middleware emits `before_request` and `after_request` checkpoints; the error handler appends failure breadcrumbs; services can opt into `@trace_execution` to capture service timing and call locations.

## Timing model
Each log includes a timing block:
- `total_ms`: wall-clock time from middleware start to completion.
- `middleware_ms`: summed time in before/after middleware hooks.
- `route_ms`: time spent inside Flask routing/view execution.
- `service_ms`: cumulative time recorded by `@trace_execution` decorators.

## Sensitive data masking
Keys containing `password`, `token`, `authorization`, `cookie`, or `csrf_token` are masked or removed across incoming and outgoing payloads. Headers drop sensitive entries entirely. File logging keeps only filenames and extensions.

## Error & validation logging
- Exceptions emit structured entries with type, message, traceback string, source file/function/line, payload snapshot, breadcrumbs, correlation IDs, and elapsed time at failure.
- Validation failures emit the `validation_failed` snapshot automatically; no route-level logging calls are required.

## Unified log shape (JSON per line)
Example (truncated for brevity):
```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "level": "INFO",
  "request_id": "ab12cd34",
  "trace_id": "ef56",
  "path": "/api/demo",
  "method": "POST",
  "incoming_payload": {"json": {"name": "Alice"}},
  "outgoing_payload": {"status_code": 201, "json": {"ok": true}},
  "breadcrumbs": [{"file": "app/logging/middleware.py", "function": "_start_observation", "line": 38, "message": "before_request:start"}],
  "validation": {},
  "timing": {"total_ms": 12, "middleware_ms": 3, "service_ms": 0, "route_ms": 9},
  "response_status": 201,
  "user_id": 42,
  "file": "middleware.py",
  "function": "_emit_final_log",
  "line": 90
}
```

## Rotation and access
- File sink: `logs/app.log.json`, rotated nightly with 4 days retained.
- Console sink: colorized output for local debugging.
- Both use the same JSON formatter; the file sink is safe for ingestion via `jq`/ELK.

## Troubleshooting
- **Duplicate logs**: ensure only `initialize_logging(app)` runs; the middleware is idempotent (`_structured_logging_installed`).
- **Missing correlation IDs**: confirm proxy/load balancer is not stripping `X-Request-ID`/`X-Trace-ID`; middleware will generate them when absent.
- **Unexpected fields**: adjust sanitizers in `app/logging/sanitizers.py` to add/remove masked keys.
- **Large bodies**: payload capture is best-effort; non-JSON bodies fall back to size-only logging.
