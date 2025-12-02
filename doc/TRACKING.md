# Request & Trace Tracking

## Overview
End-to-end tracking is automatic: every Flask request receives correlation identifiers, payload snapshots, breadcrumbs, timing, and validation diagnostics. No per-view imports or manual logging calls are required.

## Architecture (ASCII)
```
Client -> Flask -> register_logging_middleware
    -> assigns request_id/trace_id/parent_id
    -> captures inbound payloads (query, form, JSON, headers, files)
    -> executes route/services (@trace_execution supported)
    -> captures responses + validation state
    -> emits unified JSON log with breadcrumbs + timing
```

## Correlation IDs
- `request_id`: generated or honored from `X-Request-ID`; echoed in responses.
- `trace_id` / `parent_id`: generated or honored from incoming headers to support distributed tracing.
- `user_id`: resolved from Flask context when available.

## Payload tracking
- Incoming data lives in `request.meta.incoming_payload`.
- Outgoing data lives in `request.meta.outgoing_payload`.
- Breadcrumb history lives in `request.meta.trace`.
- Sensitive keys are masked/removed per `app/logging/sanitizers.py`.

## Breadcrumb rules
- Middleware appends checkpoints for start/end and validation detection.
- Error handler appends failure breadcrumbs.
- Optional `@trace_execution` decorator appends service-level breadcrumbs and accumulates `service_ms`.

## Timing breakdown
- `total_ms`: full lifecycle.
- `middleware_ms`: before/after middleware time.
- `route_ms`: Flask routing + view execution time.
- `service_ms`: time from decorated service calls.

## Validation snapshots
For 400/422 responses the logger emits:
```json
{
  "event": "validation_failed",
  "missing_fields": [],
  "invalid_fields": {},
  "allowed_values": {},
  "received_values": {...},
  "diagnostic": "Validation failed"
}
```

## Error capture
Exceptions are logged with type, message, traceback string, failing file/function/line, payload snapshot, breadcrumbs, correlation IDs, and timing at failure. Responses return JSON with the `request_id` header to aid support investigations.

## Troubleshooting
- **No breadcrumbs**: confirm middleware registration; idempotency guard prevents double registration but still allows initial wiring.
- **Missing validation block**: ensure the response status is 400/422; other statuses bypass validation extraction.
- **Unexpected masking**: extend `SENSITIVE_FIELDS` in `app/logging/sanitizers.py`.
