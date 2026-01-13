# ELITE – Coding Rules

## 1. General Principles
- Readability over cleverness
- Explicit over implicit behavior
- No hidden side effects
- Consistency across modules

---

## 2. Module Boundaries
- Routes:
  - Handle HTTP concerns only
  - No business logic
- Services:
  - Contain all business rules
  - Enforce validation and eligibility
- Models:
  - Define schema and relationships only
  - No cross-model business logic

---

## 3. Access Control
- All protected routes must declare required roles explicitly.
- Use existing decorators:
  - `require_role`
  - `admin_required`
  - `company_required`
- Never rely on frontend checks for authorization.

---

## 4. Validation and Normalization
- Validate all external input server-side.
- Normalize data before business logic execution.
- Reject invalid input early.

---

## 5. Security Rules
- CSRF tokens are mandatory for all HTML forms.
- Do not disable CSRF in any environment.
- Do not log sensitive data.

---

## 6. Logging
- All critical actions must be logged.
- Use structured logging only.
- Do not add ad-hoc print or debug logs.

---

## 7. Database Changes
- All schema changes require migrations.
- Never modify database schema manually in production.
- Maintain backward compatibility where possible.

---

## 8. Background Tasks
- Background jobs must be idempotent.
- Include correlation IDs where applicable.
- Handle retries safely.

---

## 9. Code Style
- Follow existing project formatting and naming conventions.
- Keep functions small and focused.
- Avoid deep nesting and complex conditionals.

---

## 10. Prohibited Practices
- Business logic in templates
- Direct database access in routes
- Security bypasses for convenience
- Silent failure or exception swallowing
