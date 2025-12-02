# Data Flow

The request pipeline standardizes every inbound payload before any view function or service runs.

## Lifecycle
1. **Raw extraction** (`request.raw_data`)
   - Captures JSON, form data, query params, and filtered headers without mutation.
2. **Normalization** (`request.normalized_data`)
   - Trims whitespace, converts empty strings to `None`, and normalizes `*_url` fields.
   - Records field-level deltas under `normalization` for logging.
3. **Cleaned assembly** (`request.cleaned`)
   - Merges normalized values into a single canonical mapping for routes/services.
   - Attaches diagnostics: `__original`, `__normalized`, `__diagnostics`.
4. **Validation** (`request.validation_info`)
   - Enforces required fields, choice lists, URL validity, and size limits.
   - Blocks the request with HTTP 400 if any check fails.
5. **Service consumption**
   - Routes and services read only from `request.cleaned`; no direct `request.form`/`request.get_json` access remains.

## Logging Footprint
- `incoming_payload` → `raw_data`
- `normalized_payload` → normalized view + normalization deltas
- `cleaned_payload` → canonical values consumed by services
- `validation` → diagnostics from `core.validation.validator`
- Timing includes `route_ms` and `service_ms` to correlate middleware vs business logic cost.

## Quick Reference
- Central module: `core/cleaning/request_cleaner.py`
- Validator: `core/validation/validator.py`
- Middleware: `app/logging/middleware.py` (assigns attributes and blocks invalid requests)
