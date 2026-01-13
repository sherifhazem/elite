# ELITE – Security Model

## 1. Security Principles
- Server-side enforcement of all security rules
- Deny by default
- Explicit allow via roles and decorators
- No trust in client-side validation
- Fail fast on misconfiguration

---

## 2. CSRF Protection
- CSRF protection is mandatory and enabled by default.
- Application startup fails if:
  - `WTF_CSRF_ENABLED` is disabled
  - `RELAX_SECURITY_CONTROLS` is set
- All HTML forms must include a CSRF token.
- Selected JSON API endpoints are explicitly exempted where required.

---

## 3. Authentication Model
- Authentication is handled using:
  - Signed authentication tokens stored in HttpOnly cookies
  - Flask-Login session management for browser flows
- Tokens are:
  - Scoped to the user
  - Time-bound
  - Rotated on eligible requests
- Logout clears all authentication state.

---

## 4. Authorization & Roles
- Role enforcement is implemented via decorators:
  - `require_role`
  - `admin_required`
  - `company_required`
- Role checks include:
  - Account activity status
  - Company association (for partners)
- Higher-privileged roles may satisfy lower-privileged requirements.

---

## 5. Access Control Outcomes
- `401 Unauthorized`:
  - User not authenticated
- `403 Forbidden`:
  - Inactive account
  - Role mismatch
  - Missing company association
- No sensitive error details are exposed in responses.

---

## 6. Input Validation
- All input validation is enforced server-side.
- Validation includes:
  - Required fields
  - Data types
  - Length and format constraints
- Invalid input results in:
  - Rejected request
  - Clear but non-sensitive error messages

---

## 7. Data Normalization
- Incoming data is normalized before processing:
  - Trimming whitespace
  - Canonical casing where applicable
  - Type coercion
- Normalization occurs before business logic execution.

---

## 8. Environment-Based Security
- Application startup fails without:
  - `SECRET_KEY`
- Production environment additionally requires:
  - Database configuration
  - Mail configuration
- Security-related environment variables are validated at startup.

---

## 9. Protected Areas
- Admin routes (`/admin/*`) are always protected.
- Company routes (`/company/*`) require:
  - Authenticated company role
  - Linked company record
- Member APIs enforce authentication and role checks.

---

## 10. Extension Rules
- New routes must declare required roles explicitly.
- New forms must include CSRF protection.
- No module may bypass authentication, authorization, or validation layers.
- Any relaxation of security must be explicit and environment-guarded.
