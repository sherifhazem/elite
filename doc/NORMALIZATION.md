# Normalization

All inbound request data is normalized once by the framework before any route or service sees it. The pipeline lives in `core/cleaning/request_cleaner.py` and runs inside the global logging middleware.

## Scope & Order
1. **Raw extraction** – `extract_raw_data(request)` copies JSON, form, querystring, and filtered headers into `request.raw_data`.
2. **Normalization** – `normalize_data()` trims whitespace, converts empty strings to `None`, and normalizes URL fields.
3. **Cleaned view** – `build_cleaned_data()` merges normalized values into `request.cleaned` while keeping `__original`, `__normalized`, and `__diagnostics` snapshots for debugging.

## URL Rules
- Preserve existing `http://` or `https://` schemes.
- Trim surrounding whitespace before processing.
- If a value starts with `www.` or contains a dot and no scheme, prefix `https://`.
- Empty input → `None` in `request.cleaned`.
- If parsing fails (missing `netloc` or invalid characters), keep the original for validation to reject.

## Breadcrumbs & Logging
- Breadcrumbs: `cleaning:raw_extracted`, `cleaning:url_normalized`, `cleaning:cleaned_data_built`.
- Structured log payload includes `incoming_payload` (raw), `normalized_payload`, `cleaned_payload`, and a `normalization` array of field-level deltas.
- `request.cleaned` is the canonical source for all downstream code; metadata keys prefixed with `__` hold diagnostics.

## Developer Notes
- No per-route imports are required; the middleware assigns `request.cleaned`, `request.raw_data`, and `request.normalized_data` automatically.
- Normalization applies to any field ending with `_url` (including `website_url` and `social_url`).
- Use `/test/normalizer` to view raw vs normalized echoes for manual verification.
