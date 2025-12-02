# Validation Pipeline

Validation runs after normalization and before any route handler executes. The middleware stores diagnostics on the request so services consume only cleaned, validated data.

## Steps
1. **Choice validation** – `core.validation.validator.validate()` checks `city` and `industry` against `core.choices.registry` (`get_cities`/`get_industries`).
2. **URL validation** – Any `*_url` field must parse as HTTP/HTTPS with a non-empty `netloc`.
3. **Required fields** – If required keys (email, password, company_name, phone_number, industry, city, social_url) are present but empty, they are flagged.
4. **Large text bounds** – Description/message fields over the configured limit emit `too_large` diagnostics.
5. **Diagnostics** – Results live in `request.validation_info` and the logging context.

## Responses
- Middleware blocks invalid requests automatically with HTTP 400 and a payload containing `message` and `errors` (missing fields, invalid URLs, choice failures, or oversize text).
- Breadcrumbs: `validation:choices_validated`, `validation:url_validated`, `validation:detected_failure` (when errors exist).

## Data Exposure
- `request.cleaned` is the only supported source for field access in routes/services.
- Validation details are attached to logs under `validation` and returned to clients when blocked.

## Error Shape
```json
{
  "message": "Invalid request payload.",
  "errors": [
    {"missing_fields": ["email", "password"]},
    {"invalid_urls": [{"field": "social_url", "reason": "invalid_url_format"}]},
    {"invalid_choices": [{"field": "city", "allowed_values": ["الرياض", "جدة", "الدمام"]}]},
    {"too_large": [{"field": "description", "limit": 2000, "length": 2450}]}
  ],
  "request_id": "..."
}
```

## Developer Notes
- Validators use normalized values, so whitespace/empty-string cleanup happens first.
- The middleware always sets `request.validation_info` (even when valid) to keep logs and services in sync.
- Add new required fields or text limits inside `core/validation/validator.py` to extend coverage centrally.
