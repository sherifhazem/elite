# Validation Pipeline

The validation layer consumes normalized URLs and registry-driven choices, emitting consistent diagnostics and breadcrumbs for every check.

## Behavior Overview
- **Normalized before checks:** Fields ending with `_url` (including `website_url` and `social_url`) reach forms and services with schemes added when needed.
- **Missing schemes:** Automatically prefixed with `https://` when the value has a dot or begins with `www.`.
- **Invalid URLs:** Strings without dots, invalid characters, or empty `netloc` remain unchanged and fail validation.
- **Choice validation:** Cities and industries are validated against the central registry via `validate_choice`, recording `allowed_values`, `received_value`, and reasons.
- **Raw vs validated:** Logs capture raw inputs under `incoming_payload` and the validated/clean variants under `normalized_payload` for debugging.

## Rules Matrix (URLs)
| Input | Normalized | Validation Outcome |
| --- | --- | --- |
| `www.example.com` | `https://www.example.com` | Accepted by URL validators |
| `example.com` | `https://example.com` | Accepted |
| `https://example.com` | `https://example.com` | Accepted |
| `http://example.com` | `http://example.com` | Accepted |
| `test` | `test` | Rejected (no domain) |
| `bad url` | `bad url` | Rejected (invalid characters) |

## Choice Validation
- Uses `core.choices.validate_choice` for both `city` and `industry`.
- Breadcrumbs: `validation:city_checked` and `validation:industry_checked` added automatically.
- Diagnostic payloads live under `validation.failures` with `field`, `received_value`, `allowed_values`, `reason`, and `diagnostic` when available.

## Before vs After
- **Before:** Missing schemes often triggered "invalid URL" errors even when the domain was correct; city/industry lists were scattered.
- **After:** Schemes are injected centrally and choices are enforced through a single registry, so only truly invalid data surfaces errors.

## Logging & Tracking Integration
- `incoming_payload` retains pre-normalization values for auditability.
- `normalized_payload` shows the cleaned URLs and `normalized_fields` pairs; per-field deltas live under the `normalization` block and emit a `normalization:url_fixed` breadcrumb.
- Validation snapshots reference the normalized payload so error reports align with the data that validators saw.

## Developer Notes
- No per-route imports are required; normalization is wired inside `app/logging/middleware.py` and JSON normalization in `company_registration_service`.
- Use `curl -X POST /test/normalizer -d 'website_url=www.example.com'` to observe normalization in action.
- Inspect `/dev/choices` (non-production) to confirm allowed values during validation debugging.
