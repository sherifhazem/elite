# Validation Pipeline

The validation layer now consumes URLs that were normalized in the global middleware. Missing schemes are fixed upstream, so validators focus on domain plausibility and structural soundness instead of protocol prefixes.

## Behavior Overview
- **Normalized before checks:** Fields ending with `_url` (including `website_url` and `social_url`) reach forms and services with schemes added when needed.
- **Missing schemes:** Automatically prefixed with `https://` when the value has a dot or begins with `www.`.
- **Invalid URLs:** Strings without dots, with invalid characters, or too short remain unchanged and will still fail validation.
- **Raw vs validated:** Logs capture raw inputs under `incoming_payload` and the validated/clean variants under `normalized_payload` for debugging.

## Rules Matrix
| Input | Normalized | Validation Outcome |
| --- | --- | --- |
| `www.example.com` | `https://www.example.com` | Accepted by URL validators |
| `example.com` | `https://example.com` | Accepted |
| `https://example.com` | `https://example.com` | Accepted |
| `http://example.com` | `http://example.com` | Accepted |
| `test` | `test` | Rejected (no domain) |

## Before vs After
- **Before:** Missing schemes often triggered "invalid URL" errors even when the domain was correct.
- **After:** Schemes are injected centrally; only structurally broken URLs surface validation errors.

## Logging & Tracking Integration
- `incoming_payload` retains pre-normalization values for auditability.
- `normalized_payload` shows the cleaned URLs; per-field deltas live under the `normalization` block and emit a `normalization:url_fixed` breadcrumb.
- Validation snapshots reference the normalized payload so error reports align with the data that validators saw.

## Developer Notes
- No per-route imports are required; normalization is wired inside `app/logging/middleware.py`.
- Use `curl -X POST /test/normalizer -d 'website_url=www.example.com'` to observe normalization in action.
