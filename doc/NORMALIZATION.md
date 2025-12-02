# URL Normalization

Centralized URL normalization runs globally before validation to ensure consistent handling of user-submitted URLs without requiring per-route helpers.

## Rules
- Preserve existing `http://`, `https://`, or `ftp://` schemes.
- Trim whitespace automatically.
- If a value starts with `www.` → prefix `https://`.
- If a value has a dot but no scheme → prefix `https://`.
- Empty input returns an empty string.
- Obvious non-URLs (no dots, too short, invalid characters) remain unchanged so validation can flag them.

## Architecture (ASCII)
```
[Client]
   |
   v
[Flask Request]
   |
   v
[Logging Middleware]
   |- capture incoming_payload (raw)
   |- normalize form *_url fields
   |- record normalization breadcrumb + deltas
   |- capture normalized_payload (post-normalization)
   v
[Validation / Services]
   |
   v
[Structured Logs + Responses]
```

## Examples
| Input | Output |
| --- | --- |
| `www.example.com` | `https://www.example.com` |
| `example.com` | `https://example.com` |
| `https://example.com` | `https://example.com` |
| `http://example.com` | `http://example.com` |
| `test` | `test` |

## Logging & Tracking
- `incoming_payload`: shows raw URL values before normalization.
- `normalized_payload`: shows post-normalization values plus `normalized_fields` for quick inspection.
- `normalization`: array of per-field deltas (`field`, `from`, `to`).
- Breadcrumb `normalization:url_fixed` is added when any field changes.

## Developer Usage
- Normalization is centralized in `core/normalization/url_normalizer.py` and wired via `app/logging/middleware.py`.
- No imports are required inside routes or services; the middleware updates `request.form` before validators run.
- Test quickly with `curl -X POST /test/normalizer -d 'social_url=www.example.com'` to see the normalized echo.
