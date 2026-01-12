# Request & Usage Tracking

## Overview
End-to-end tracking is automatic and centralized.

The system tracks:
- Technical request lifecycle (requests, validation, errors, timing)
- Business-level usage events derived from verified actions

No per-view imports or manual logging calls are required.

---

## Architecture (ASCII)
Client
-> Flask
-> register_logging_middleware
-> assigns request_id / trace_id / parent_id
-> captures inbound payloads
-> executes route/services
-> captures validation & timing
-> emits unified JSON log

Verified Usage Events
-> derived from successful requests
-> persisted for activity evaluation

yaml
Copy code

---

## Correlation Identifiers
- `request_id`: Generated or honored from `X-Request-ID`, echoed in responses.
- `trace_id` / `parent_id`: Generated or honored for distributed tracing.
- `user_id`: Resolved from Flask context when authenticated.
- `company_id`: Attached when request is associated with a partner/store.

These identifiers allow full correlation between technical logs and usage records.

---

## Payload Tracking
- Incoming data → `request.meta.incoming_payload`
- Outgoing data → `request.meta.outgoing_payload`
- Breadcrumb history → `request.meta.trace`
- Sensitive keys are masked or removed via `app/logging/sanitizers.py`

Payload tracking is used for:
- Debugging
- Auditability
- Validation diagnostics

It is NOT used to determine privileges or incentives.

---

## Breadcrumb Rules
- Middleware appends start/end checkpoints.
- Validation failures append explicit breadcrumbs.
- Error handler appends failure breadcrumbs.
- Optional `@trace_execution` decorator appends service-level breadcrumbs and accumulates `service_ms`.

Breadcrumbs describe execution flow only, not business decisions.

---

## Timing Breakdown
- `total_ms`: Full request lifecycle.
- `middleware_ms`: Pre/post middleware time.
- `route_ms`: Flask routing + view execution.
- `service_ms`: Aggregated time from decorated services.

Timing data is used for observability and performance tuning only.

---

## Validation Snapshots
For 400 / 422 responses, the logger emits:
```json
{
  "event": "validation_failed",
  "missing_fields": [],
  "invalid_fields": {},
  "allowed_values": {},
  "received_values": {},
  "diagnostic": "Validation failed"
}
Validation failures do NOT generate usage events.

Usage Tracking (Business Layer)
Usage tracking is derived from verified actions only.

Principles:

A usage event is recorded only after successful verification.

Usage events are the single source of truth for:

User activity (active / inactive)

Partner activity (active / inactive)

Incentive eligibility

Usage tracking does NOT depend on:

Membership levels

Manual flags

Static discounts

Error Capture
Exceptions are logged with:

Exception type and message

Traceback (string)

Failing file / function / line

Payload snapshot

Breadcrumbs

Correlation identifiers

Timing at point of failure

Error responses include the request_id header to support investigation.

Troubleshooting
No breadcrumbs: Confirm middleware registration; idempotency guard prevents double registration.

Missing validation block: Ensure response status is 400 or 422.

Unexpected masking: Extend SENSITIVE_FIELDS in app/logging/sanitizers.py.

Usage not recorded: Confirm verification completed successfully; unverified requests never create usage events.