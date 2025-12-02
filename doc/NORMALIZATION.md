# URL Normalization

Centralized URL normalization runs globally before validation to ensure consistent handling of user-submitted URLs without requiring per-route helpers.

## Rules
- Preserve existing `http://` or `https://` schemes.
- Trim whitespace automatically.
- If a value starts with `www.` → prefix `https://`.
- If a value has a dot but no scheme → prefix `https://`.
- Empty input returns an empty string.
- If the parsed URL has no `netloc` or contains invalid characters, return the raw input so validation can fail later.

## Behavior Table
| Input | Normalized | Notes |
| --- | --- | --- |
| `www.example.com` | `https://www.example.com` | `www.` auto-prefixed |
| `example.com` | `https://example.com` | dot triggers prefix |
| `https://example.com` | `https://example.com` | untouched |
| `http://example.com` | `http://example.com` | scheme preserved |
| `  ftp://example.com  ` | `ftp://example.com` | whitespace trimmed, unsupported scheme left as-is for validation |
| `bad url` | `bad url` | invalid characters keep raw for later rejection |

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
[Services (JSON + forms)]
   |- additional JSON normalization for *_url payloads
   v
[Validation]
   |
   v
[Structured Logs + Responses]
```

## Logging & Tracking
- `incoming_payload`: shows raw URL values before normalization.
- `normalized_payload`: shows post-normalization values plus `normalized_fields` as `[raw, normalized]` pairs for quick inspection.
- `normalization`: array of per-field deltas (`field`, `from`, `to`).
- Breadcrumb `normalization:url_fixed` is added when any field changes.

## Developer Usage
- Normalization is centralized in `core/normalization/url_normalizer.py` and wired via `app/logging/middleware.py` (forms) plus `company_registration_service` (JSON payloads).
- Forms receive normalized data automatically because the middleware updates `request.form` before validators run.
- Test quickly with `curl -X POST /test/normalizer -d 'social_url=www.example.com'` to see the normalized echo.
