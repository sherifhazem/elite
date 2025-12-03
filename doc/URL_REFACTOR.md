# URL Refactor Guide

## Frontend normalization rules
- Execute inside the `register-company-form` submit handler so the values are corrected before transmission.
- Preserve values that already start with `http://` or `https://`.
- Prepend `https://` when the value starts with `www.`.
- Prepend `https://` for any value containing a dot but missing a scheme.
- When the value starts with a digit followed by a dot, prepend `https://www.` to keep numeric domains usable.
- Leave empty values empty.
- All other inputs are left unchanged.

## Backend normalization rules
- Trim surrounding whitespace before processing.
- Return an empty string for empty inputs.
- Keep inputs that already start with `http://` or `https://`.
- Prefix `https://` for inputs that start with `www.`.
- Prefix `https://www.` when the first character is numeric.
- Prefix `https://` for any value containing a dot but lacking a scheme.
- Otherwise, return the original string so downstream validation can respond appropriately.

## Validation rules
- Empty URL fields are accepted.
- Values starting with `http://` or `https://` are accepted without further checks.
- Values containing a dot with at least two characters before the first dot are accepted.
- Reject only when the value lacks any dot **or** contains spaces, quotes, or backslashes.
- No DNS lookups or `urlparse`-style netloc checks are performed to allow non-standard yet real-world domains.

## Before/After examples
- `www.123.com` → `https://www.123.com`
- `123.com` → `https://123.com`
- `1.com` → `https://www.1.com`
- `cars.sa` → `https://cars.sa`
- `http://example.org` → `http://example.org` (unchanged)
- `bad host.com` → rejected by validation because of the space

## Why numeric domains need special handling
Many registries allow numeric-leading domains (for example `1.com`). Without explicitly prefixing `https://www.` when the first character is a digit, the browser and backend libraries may misinterpret the value or treat it as malformed. The normalization layer guarantees these domains become conventional URLs before validation or persistence.

## Why strict `urlparse` validation is disabled
The previous approach relied on `urlparse`-derived netloc checks, which rejected perfectly valid domains without schemes or short TLD pairs. The new logic focuses on simple safety (no spaces/quotes/backslashes) while allowing a broad set of real-world and numeric domains that users submit.

## Validation edge cases
- Strings with embedded whitespace (including tabs) are invalid.
- Quotes (`'` or `"`) and backslashes (`\\`) invalidate the value.
- Single-character prefixes before a dot (e.g., `a.com`) are rejected unless a scheme is present.
- Lists of URLs follow the same rules item-by-item; any invalid entry flags the field.
- Empty strings and `None` remain valid to allow optional fields.

## Troubleshooting
- If URLs are still rejected, confirm the middleware is populating `request.cleaned` and services read from it (not `request.form`).
- Verify the frontend script is loaded and the submit handler runs; normalized values should be visible in the network payload.
- Ensure any custom code imports the shared helpers only from:
  - `app.core.normalization.url_normalizer.normalize_url`
  - `app.core.validation.validator.validate`
  - `app.core.cleaning.request_cleaner.build_cleaned_payload`
- When debugging unexpected rejections, log the normalized value after cleaning to see whether invalid characters are present.
