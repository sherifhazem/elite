# ELITE – Logging & Observability

## 1. Design Goals
- Full request traceability
- Role- and user-aware activity auditing
- Zero business logic in logging
- No sensitive data leakage
- Structured, machine-readable logs

---

## 2. Structured Logging
- Logging format: JSON
- Outputs:
  - Console
  - `logs/app.log.json`
- Each log entry includes:
  - Timestamp
  - Log level
  - Request ID
  - Trace ID
  - Parent ID (if present)
  - HTTP method and path
  - User ID (if authenticated)
  - Role and company context (when applicable)

---

## 3. Request Correlation
- Supported headers:
  - `X-Request-ID`
  - `X-Trace-ID`
  - `X-Parent-ID`
- If headers are missing:
  - IDs are generated at request entry
- IDs are propagated to:
  - Downstream logs
  - HTTP responses

---

## 4. Request Lifecycle Tracking
1. Incoming request enters Flask
2. Logging middleware initializes request context
3. Request metadata is normalized and sanitized
4. Route handler executes
5. Response metadata is captured
6. Final structured log entry is emitted

---

## 5. ActivityLog Model
- ActivityLog persists critical domain events:
  - Usage-code verification attempts
  - Redemption confirmations
  - Admin actions (e.g. report exports)
- Stored fields include:
  - Actor (user ID, role, company ID)
  - Action type
  - Target entity
  - Result (success / failure)
  - Timestamp

---

## 6. Security and Privacy
- Sensitive fields are masked or excluded:
  - Passwords
  - Tokens
  - Raw payloads
- Logging never includes:
  - Authentication secrets
  - Full request bodies for auth endpoints
- Activity logs are immutable once written.

---

## 7. Admin Visibility
- Admin users can review activity logs via:
  - `/admin/activity-log`
- Logs are filterable by:
  - User
  - Company
  - Action type
  - Time range

---

## 8. Operational Usage
- Logs are suitable for:
  - Debugging
  - Security audits
  - Usage analysis
- JSON format allows:
  - External log aggregation
  - Alerting systems
  - Long-term storage

---

## 9. Extension Rules
- New critical actions must emit ActivityLog entries.
- Logging middleware must not be bypassed.
- Any new background job must include correlation IDs where applicable.
