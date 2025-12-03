# Company Registration Pipeline

This document captures the end-to-end flow for company registration, including how URLs are normalized, validated, and transported through the system.

## Frontend URL normalization

Implemented in `app/modules/members/static/members/js/company_registration_form.js`:

- Trim whitespace from inputs before submission.
- If the value starts with `http://` or `https://`, keep it unchanged.
- If the value starts with `www.`, prepend `https://`.
- If the first character is a digit, prepend `https://www.`.
- If the value contains a dot, prepend `https://`.
- If the field is empty, leave it empty.
- The normalized values are written back to the form fields so the submitted payload matches the cleaned version.

## Backend URL normalization

Centralized in `app/core/normalization/url_normalizer.py`:

- Strip leading and trailing whitespace.
- Empty values return an empty string.
- Values that already start with `http` are returned unchanged.
- Values starting with `www.` are prefixed with `https://`.
- Values beginning with a digit are prefixed with `https://www.`.
- Values containing a dot are prefixed with `https://`.
- All other values are returned as provided.

## Backend relaxed URL validation

Implemented in `app/core/validation/validator.py`:

- Empty values are valid.
- Any value starting with `http://` or `https://` is valid.
- Any value containing at least one dot is valid.
- URLs are rejected only when they contain invalid characters (spaces, quotes, or backslashes) **or** when they lack both a scheme and a dot.

This ensures normalized links such as `https://123.com`, `https://www.123.com`, `https://cars.sa`, and `https://1.com` pass validation without WTForms conflicts.

## Interaction between layers

1. **Incoming request**: Captured as `request.incoming_payload` for logging.
2. **Normalization**: URL fields are normalized on the frontend and again in the backend; the backend result is recorded as `request.normalized_payload`.
3. **Cleaning**: `request.cleaned` holds the post-normalization, cleaned payload used by service layers.
4. **WTForms**: The company registration form no longer performs URL validation. It only checks required fields, letting backend normalization and validation govern URL correctness.
5. **Service layer**: Services read from `request.cleaned` (or the cleaned payload handed in) to ensure the normalized values flow into persistence and notifications.

## Before/After examples

| Input | Frontend submission | Backend normalized | Validation result |
| --- | --- | --- | --- |
| ` www.example.com ` | `https://www.example.com` | `https://www.example.com` | Valid |
| `123.com` | `https://www.123.com` | `https://www.123.com` | Valid |
| `cars.sa` | `https://cars.sa` | `https://cars.sa` | Valid |
| `https://1.com` | `https://1.com` | `https://1.com` | Valid |
| `` (empty) | `` | `` | Valid |

## Troubleshooting

- **WTForms URL validator blocked numeric domains**: Strict WTForms URL validation rejected numeric-leading domains (e.g., `123.com`). Removing the `URL()` validator avoids conflicts with our relaxed backend validator.
- **Validation moved to the backend**: Consolidating validation prevents duplicated logic and ensures consistent handling for API and HTML submissions.
- **Normalization ensures consistency**: Applying normalization in both frontend and backend yields uniform URLs regardless of user input quirks, leading to consistent logging, validation, and storage.
