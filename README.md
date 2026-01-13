# ELITE

## 1. Project Overview
ELITE is a Flask web application that manages discount offers, membership access, partner portals, and administrative operations for a role-based discounts platform.

**Target users:**
- **Admin:** manages users, companies, offers, settings, reports, and activity logs.
- **Partner (Company):** manages company profile, offers, redemptions, and usage codes through the company portal.
- **Member:** registers, logs in, browses offers, activates redemptions, verifies usage codes, and manages profile data through the member portal.

**Core value proposition (technical):**
A centralized, role-driven platform with shared services for offers, redemptions, usage-code verification, and structured activity logging built on Flask blueprints and SQLAlchemy models.

---

## UI Theme

The member portal UI theme is centralized in `app/modules/members/static/members/css/portal_layout.css`. Update the design tokens in the `:root` block to adjust colors and sizing across the portal without changing template markup.

**Where to edit:**
- **Colors:** `--bg-primary`, `--text-primary`, `--gold`, `--royal-black`, `--soft-green`, `--card-bg`, `--muted-text`.
- **Sizing & layout:** `--radius-card`, `--radius-pill`, `--shadow-soft`, `--space-xs`, `--space-sm`, `--space-md`, `--space-lg`, `--container-width`.

---

## Mobile Shell (Members Portal)

The Members Portal shell lives in `app/modules/members/templates/members/portal/base.html`. It is mobile-first, capped at 420px, enforces full-height layout with no horizontal overflow, and keeps the bottom navigation visible with safe-area padding for modern devices.

**Key behaviors:**
- Use RTL (`dir="rtl"`) for Arabic layouts while keeping Font Awesome icons intact.
- Keep the bottom navigation markup and links unchanged; only update styling for translucent dark background, rounded container, and gold active icons.
- Avoid loading new fonts; use `Tajawal` or web-safe fallbacks already available in the stack.

---

## Dark Mode (Members Portal)

The Members Portal uses a permanent dark theme by default, driven entirely by CSS tokens in `app/modules/members/static/members/css/portal_layout.css`. Templates must only inherit these styles (no inline overrides) so the tokens remain the single source of truth.

**Reference colors**
- Primary Background: `#1C2D45` (`--bg-primary`)
- Headings & Text: `#FFFFFF` (`--text-primary`)
- Gold: `#D4AF37` (`--gold`)
- Royal Black: `#111111` (`--royal-black`)
- Soft Green: `#4CAF50` (`--soft-green`)
- Card Surface: `#F5F1E8` (`--card-bg`)
- Muted Text: `#C9D2E3` (`--muted-text`)

**How to adjust**
- Update the tokens in the `:root` block (e.g., `--bg-primary`, `--text-primary`, `--card-bg`, `--muted-text`) to tune the dark palette without changing templates.
- Card surfaces inherit from `--card-bg` and rely on portal text variables for contrast, keeping the dark shell and light cards readable across the portal.

---

## Auth UI (Members)

Members authentication screens reuse the same Dark Design System tokens defined in `app/modules/members/static/members/css/portal_layout.css`. The Auth layouts load these tokens directly and apply them through `app/modules/members/static/members/css/auth_layout.css` to keep login, registration, and password flows visually consistent with the Members Portal.

Auth UI does not include a splash screen.

Flash messages in Auth UI are custom-styled to match the Dark Design System rather than relying on Bootstrap defaults.

---

## 2. System Architecture

### Flask application and extensions
- Application factory: `app.create_app` initializes configuration and extensions.
- Core extensions include:
  - SQLAlchemy
  - Flask-Migrate
  - Flask-Login
  - CSRF protection
  - Mail
  - Celery (when configured)
- Structured logging middleware is registered at application startup.

### Module structure
- `app/modules/members`
  - Member-facing portal, authentication, offers, redemptions, notifications, and APIs.
- `app/modules/companies`
  - Company registration, partner portal, offers, redemptions, and usage codes.
- `app/modules/admin`
  - Admin dashboard, user/company management, settings, reports, notifications, and activity log views.

### Services and data layer
- Shared business logic resides in `app/services`.
- Module-specific services exist under `app/modules/*/services`.
- Data persistence is handled via SQLAlchemy models in `app/models`.

### Logging and request lifecycle
- A centralized logging middleware captures request and trace context.
- `before_request` hooks:
  - Attach the current user
  - Resolve roles
  - Enforce access control
- `after_request` hooks:
  - Refresh authentication cookies when applicable
  - Emit structured request logs with correlation IDs

### Redis (optional)
- Redis is optionally used for role-permission and admin setting storage.
- Enabled only when `REDIS_URL` is configured.

---

## 3. Roles & Access Model

### Admin
**Capabilities:**
- Manage users, roles, companies, offers, settings, communications, reports, and activity logs.
- View dashboards and export reports.

**Restrictions:**
- Requires an authenticated and active account with `admin` or `superadmin` role.
- Access enforced via `admin_required`.

**Entry points:**
- `/admin/`
- `/admin/dashboard`
- `/admin/users`
- `/admin/companies`
- `/admin/offers`
- `/admin/settings`
- `/admin/reports`
- `/admin/activity-log`

---

### Partner (Company)
**Capabilities:**
- Access the company portal.
- Manage company settings and offers.
- Generate and manage usage codes.
- Review and confirm redemptions.

**Restrictions:**
- Requires authentication with the `company` role.
- Must be linked to a valid `company_id`.
- Enforced via `company_required`.

**Entry points:**
- `/company/`
- `/company/dashboard`
- `/company/offers`
- `/company/usage-codes`
- `/company/redemptions`
- `/company/settings`
- `/company/complete_registration/<company_id>`

---

### Member
**Capabilities:**
- Register and authenticate.
- Browse offers.
- Activate redemptions.
- Verify usage codes.
- Manage profile and notifications.

**Restrictions:**
- Protected APIs require an authenticated and active account.
- Unauthorized access returns `401`; role mismatches return `403`.

**Entry points:**
- `/portal/`
- `/portal/offers`
- `/portal/profile`
- `/portal/notifications`
- `/api/redemptions`
- `/api/usage-codes/verify`
- `/api/auth/register`
- `/api/auth/login`
- `/login`

---

## 4. Core Functional Flows

### Authentication and sessions
- Authentication uses a signed token stored in an HttpOnly cookie combined with Flask-Login sessions for browser flows.
- Auth cookies are refreshed on eligible authenticated requests.
- Logout clears session state and authentication cookies.

### Registration
- **Member registration**
  - API: `POST /api/auth/register`
  - Browser form: `GET|POST /register/member`
- **Company registration**
  - API: `POST /api/companies/register`
  - Completion and correction: `GET|POST /company/complete_registration/<company_id>`

### Offer lifecycle
- Partners create, edit, and delete offers through the company portal.
- Offers include base discount, availability dates, status, and classifications.
- Members browse offers via the portal and offers API.
- Admins manage offers globally through the admin dashboard.

### Usage-code verification
- Partners generate short-lived usage codes via the company portal.
- Members verify codes via `POST /api/usage-codes/verify`.
- Verification enforces:
  - Code validity and expiry
  - Activity eligibility rules
  - Per-window usage limits
- All attempts are recorded in `ActivityLog`.

### Redemption flow
- Members activate offers via `POST /api/redemptions`.
- A redemption code and QR token are generated.
- Partners confirm usage via `PUT /api/redemptions/<code>/confirm`.
- QR codes are served via `GET /api/redemptions/<code>/qrcode`.

---

## 5. Security Model

### CSRF protection
- CSRF protection is mandatory.
- Application startup fails if CSRF is disabled.
- Selected JSON API endpoints are explicitly exempted where required.

### Role-based access control
- Access control is enforced using:
  - `require_role`
  - `admin_required`
  - `company_required`
- Role checks include account activity and company association.

### Environment-based security
- Application startup fails without `SECRET_KEY`.
- Production mode requires database and mail configuration.
- `RELAX_SECURITY_CONTROLS` is explicitly rejected.

### Blocked behaviors
- Unauthenticated access to protected routes returns `401` or redirects to login.
- Inactive accounts and role mismatches return `403`.

---

## 6. Configuration & Environment

### Required environment variables
- `SECRET_KEY`
- `SQLALCHEMY_DATABASE_URI` (required in production)

### Optional configuration
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- Mail settings: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- `TIMEZONE`
- `WTF_CSRF_ENABLED` (guarded; disabling CSRF aborts startup)

### Environment safeguards
- Production startup enforces database and mail configuration.
- CSRF remains enforced in all environments.

---

## 7. Database & Migrations

### ORM usage
- SQLAlchemy models define users, companies, offers, redemptions, usage codes, notifications, and activity logs.

### Migration strategy
- Database schema changes are managed using Flask-Migrate (Alembic).

### Data integrity rules
- Unique constraints apply to:
  - User credentials
  - Company identifiers
  - Redemption codes and QR tokens
  - Admin setting keys

### Usage codes
- Usage codes are numeric 4–5 digit strings.
- Expiry and usage limits are configurable via admin settings.
- Although a `code_format` setting exists, verification currently enforces numeric-only codes.

---

## 8. Logging & Observability
- ActivityLog records:
  - Admin actions
  - Usage-code verification attempts
- Structured JSON logs are written to:
  - Console output
  - `logs/app.log.json`
- Correlation headers:
  - `X-Request-ID`
  - `X-Trace-ID`
  - `X-Parent-ID`
- Admin UI access:
  - `/admin/activity-log`

---

## 9. Operational Notes

### Known limitations
- Membership upgrade and incentive calculation logic is not fully implemented.
- Discounts are applied directly from offer configuration without dynamic calculation.
- Usage-code format settings allow letter-prefixed codes, but verification currently accepts numeric-only codes.

### Safe extension boundaries
- Member features: `app/modules/members`
- Partner features: `app/modules/companies`
- Admin features: `app/modules/admin`
- Shared logic: `app/services`
- Data models: `app/models`

---

## 10. Documentation Changelog
- **Date:** 2026-01-13  
- **Summary:** Complete rewrite of README to reflect actual code behavior and architecture  
- **Reason:** Establish a single, authoritative source of truth for the ELITE platform
