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

## Request Cleaning Pipeline
- **Centralized cleaning:** `core/cleaning/request_cleaner.py` extracts raw payloads, normalizes strings/URLs, and builds `request.cleaned` with diagnostics before any route executes.
- **Automatic validation:** `core/validation/validator.py` runs in middleware to enforce required fields, registry choices, URL validity, and text limits; failures return HTTP 400 with structured errors.
- **Canonical data:** Routes and services must read from `request.cleaned` (never `request.form`/`request.get_json`), ensuring every service operates on normalized input.
- **Learn more:** See `doc/DATA_FLOW.md`, `doc/NORMALIZATION.md`, and `doc/VALIDATION.md` for the full lifecycle and rule tables.

## Auto URL Normalization
- **Centralized module:** `core/normalization/url_normalizer.py` automatically normalizes any incoming field ending with `_url` (including `website_url` and `social_url`).
- **Rules:** Preserves existing `http://`/`https://`, prefixes `https://` when a dot is present or the value starts with `www.`, trims whitespace, and returns raw values that cannot be parsed (invalid characters or missing `netloc`) so validation can surface errors.
- **Middleware-owned:** Normalization runs in the global `app/logging/middleware.py` before validation so forms, JSON payloads, and services all receive already-normalized URLs without any per-route helpers.
- **Logging:** Logs include the raw payload in `incoming_payload`, the corrected values in `normalized_payload.normalized_values`, and before/after pairs in `normalized_payload.normalized_fields` with breadcrumb `normalization:url_fixed`.
- **Developer probe:** POST to `/test/normalizer` (via `routes/dev_tools/normalization_test.py`) to observe normalized form/json echoes for manual testing.

## Central Choices Registry
- **Source of truth:** `core/choices/registry.py` declares authoritative `CITIES` and `INDUSTRIES` defaults used to seed settings storage and feed forms/services.
- **Accessors:** Use `get_cities()` / `get_industries()` to fetch managed values (settings-backed, registry fallback) and `validate_choice()` to enforce selections with logging breadcrumbs (`validation:city_checked`, `validation:industry_checked`).
- **Validation logging:** Choice checks populate `validation` diagnostics with `allowed_values`, `received_value`, and reasons for easier debugging.

## Admin Settings Management
- **Single UI:** `/admin/settings` renders registry-driven lists for cities and industries with tabbed navigation and AJAX forms—no page reloads.
- **Endpoints:**
  - Add: `/admin/settings/add_city`, `/admin/settings/add_industry`
  - Update: `/admin/settings/update_city`, `/admin/settings/update_industry`
  - Delete: `/admin/settings/delete_city`, `/admin/settings/delete_industry`
- **Registry-first:** Lists come directly from `core.choices.registry.CITIES/INDUSTRIES`; mutations happen in-memory and are logged with `admin_settings_action`, `status`, `value`, and `reason` (e.g., `duplicate_value`, `empty_value`).
- **Diagnostics:** `/dev/settings_status` (non-production) reports registry contents and counts alongside `/dev/choices`.
- **ASCII preview:**
```
[مدن] [مجالات العمل]
➕ إضافة مدينة | جدول المدن (تعديل/حذف)
➕ إضافة مجال  | جدول المجالات (تعديل/حذف)
تحديث فوري + Toast للنجاح + تنبيهات للأخطاء
```

## Monitoring Endpoints
- **Normalization probe:** `/test/normalizer` echoes raw vs normalized payloads for quick checks.
- **Choices explorer:** `/dev/choices` (non-production) returns the active registry payload `{cities, industries}` with `source: core.choices.registry` for validation/debugging without authentication.

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
