# ELITE Platform

## 1. Project Overview
- منصة ELITE توفّر بوابة للشركات والأعضاء لإدارة العروض والخصومات مع نظام مراجعة وتفعيل متكامل.
- What ELITE does today:
  - Provides a member portal for browsing offers, activating redemptions, and viewing notifications. 
  - Provides a company (partner) portal for managing offers, monitoring redemptions, and issuing usage verification codes. 
  - Provides an admin dashboard for managing users, companies, offers, settings, reports, and communications.
  - Exposes JSON APIs for offers, redemptions, usage-code verification, and notifications.
- Target users:
  - **Admin** (admin/superadmin) operating the platform.
  - **Partner (Company)** managing offers and redemptions.
  - **Member** browsing offers and activating redemptions.
- Core value proposition (non-marketing): centralized offer management, onboarding, and verification workflows with role-based access and audit logging.

## 2. System Architecture
- High-level components:
  - Flask application factory initializes configuration, extensions (DB, mail, CSRF, login), logging middleware, and blueprints. 
  - Module packages:
    - `app/modules/members`: public site, member auth, portal, and member APIs.
    - `app/modules/companies`: company registration and company portal.
    - `app/modules/admin`: admin dashboard, reports, settings, and communications.
  - Service layer for business logic (registration, redemption, usage codes, admin settings).
  - Data layer using SQLAlchemy models with Flask-Migrate for migrations.
  - Redis-backed role permission storage and JSON logging to `logs/app.log.json`.
- Module responsibility boundaries:
  - **Members**: registration/login, portal pages, offers list, redemptions API, usage-code verification, notifications API.
  - **Companies**: registration request intake, portal dashboards, offer CRUD, redemption verification, usage codes.
  - **Admin**: user/company/offer management, site settings, role permissions, analytics/reports, activity log.
- Request lifecycle (request → response):
  - Structured logging middleware builds request/trace context, normalizes/cleans payloads, and validates input before route handlers run.
  - `before_request` attaches `g.current_user`, resolves roles, and enforces protected `/admin` and `/company` access with 401/403 responses for unauthenticated/inactive users.
  - Route handlers process the request and return responses.
  - `after_request` refreshes auth cookies for authenticated users and logs structured request cycles with request/trace IDs.

## 3. Roles & Access Model
- **Admin**
  - Capabilities:
    - Access admin dashboard, users, companies, offers, settings, reports, activity log, and communications views.
    - Configure admin settings (activity rules, verification settings, offer type toggles) and managed lists (cities/industries).
    - Superadmin-only: manage role permissions.
  - Restrictions:
    - Requires authenticated, active admin/superadmin session.
    - Non-superadmin users cannot modify superadmin accounts.
  - Entry points:
    - `/admin/`, `/admin/dashboard`, `/admin/users`, `/admin/companies`, `/admin/offers`, `/admin/reports`.
- **Partner (Company)**
  - Capabilities:
    - Access company dashboard, manage offers, view redemption history, verify/confirm redemptions, and generate usage codes.
    - Complete correction requests via `/company/complete_registration/<company_id>`.
  - Restrictions:
    - Requires authenticated, active company account with a linked `company_id`.
    - Suspended companies are redirected away from portal access.
  - Entry points:
    - `/company/dashboard`, `/company/offers`, `/company/redemptions`, `/company/usage-codes`, `/company/register`.
- **Member**
  - Capabilities:
    - Access member portal, browse offers, activate redemptions, verify usage codes, and view notifications.
  - Restrictions:
    - Requires authenticated, active member account; role-gated for redemption and usage-code verification.
  - Entry points:
    - `/portal`, `/portal/offers`, `/api/redemptions`, `/api/usage-codes/verify`, `/api/notifications`.

## 4. Core Functional Flows
- Authentication & sessions:
  - API login issues a JWT token, sets an HttpOnly cookie, and returns a role-based redirect URL.
  - Authenticated requests refresh the auth cookie automatically.
  - Logout clears session state, clears auth cookies, and redirects to the login page.
  - Password reset flow: request reset → email link to `/reset-password/<token>` → POST to `/api/auth/reset-password/<token>`.
  - Email verification activates user accounts via `/api/auth/verify/<token>`.
- Registration:
  - Member registration via `/api/auth/register` (JSON) or `/register/member` (HTML form).
  - Company registration via `/company/register` with validation for phone number, city, and industry choices; creates a pending company with an inactive owner and notifies admins.
  - Company correction flow allows resubmission via `/company/complete_registration/<company_id>`.
- Offer lifecycle:
  - Companies create, edit, and delete offers through the company portal; offer classifications are enforced by admin settings and blocked if disabled.
  - Admins manage global offers in the admin dashboard and can broadcast offer notifications.
  - Members consume offers through the portal and `/api/offers` list endpoint; discounts remain based on `base_discount`.
- Usage / verification logic:
  - Partners generate time-limited usage codes; any existing active code is expired when a new one is created.
  - Members verify usage codes for a selected offer; eligibility checks apply (active member/partner rules and offer classification toggles).
  - Verification results include `valid`, `invalid`, `expired`, `usage_limit_reached`, or `not_eligible` and are logged in `ActivityLog`.
  - Redemption flow: members activate an offer to receive a redemption code and QR token; companies verify and confirm redemption usage.
- Activity logging:
  - `ActivityLog` captures usage-code attempts and report export events.
  - Admins can review activity logs from the admin panel.

## 5. Security Model
- CSRF enforcement (mandatory):
  - CSRF protection is enabled by default and startup fails if it is disabled or if relaxed security controls are enabled.
  - Some auth API endpoints explicitly exempt CSRF for JSON workflows.
- Role-based access control:
  - `admin_required`, `company_required`, and `require_role` decorators enforce role checks and active-account status.
  - The role access matrix allows higher-privileged roles to satisfy lower-privileged requirements.
- Environment-based configuration:
  - Production startup requires a `SECRET_KEY`, database URL, and mail configuration before the app boots.
- Explicitly blocked behaviors:
  - Unauthenticated access to `/admin` and `/company` (outside the exempt paths) is rejected with 401.
  - Inactive accounts are blocked with 403 for protected routes.
  - Company portal access is denied without a company role and linked `company_id`.

## 6. Configuration & Environment
- Required environment variables:
  - `SECRET_KEY` (always required; startup aborts if missing).
  - In production: `SQLALCHEMY_DATABASE_URI`, `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`.
- Additional configuration knobs (optional but supported):
  - `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `TIMEZONE`.
  - `MAIL_DEFAULT_SENDER`, `MAIL_PORT`, `MAIL_USE_TLS`.
  - `RELAX_SECURITY_CONTROLS` and `WTF_CSRF_ENABLED` (guarded; disabling CSRF causes startup failure).
  - `ADMIN_CONTACT_EMAIL` (used for company registration notifications).
- Runtime assumptions:
  - SQL database accessible via SQLAlchemy.
  - Redis available for role permission storage.
- Production vs development safeguards:
  - Dev-only blueprints are registered only when `ENV != "production"`.

## 7. Database & Migrations
- ORM usage:
  - SQLAlchemy models back users, companies, offers, offer classifications, redemptions, notifications, usage codes, permissions, admin settings, lookup choices, and activity logs.
- Migration strategy:
  - Flask-Migrate (Alembic) is configured via the `migrations/` directory.
- Data integrity rules (as implemented):
  - Unique constraints on user email/username, company name, lookup choices (`list_type` + `name`), redemption codes, and offer classification per offer.
  - Usage codes are 4–5 digit strings linked to companies with expiration timestamps.

## 8. Logging & Observability
- ActivityLog behavior:
  - Usage-code attempts, report exports, and related metadata are stored in `activity_log`.
- Request tracing:
  - Structured logging emits JSON to `logs/app.log.json` and propagates `X-Request-ID`, `X-Trace-ID`, and `X-Parent-ID` headers.
- Admin visibility:
  - Admins can view the activity log at `/admin/activity-log`.

## 9. Operational Notes
- Known limitations (visible in code):
  - Membership upgrade logic and incentive calculations are placeholder implementations; upgrade requests are not allowed and discounts remain based on `base_discount`.
- Safe extension boundaries:
  - Add new role-guarded routes using existing access-control decorators.
  - Store new admin-configurable settings in `AdminSetting` and role permissions in Redis.
  - Maintain request validation/cleaning through the existing middleware stack.

## 10. Documentation Changelog
- **2026-01-13**
  - Summary: Rewrote README to match current code behavior, architecture, roles, flows, security, configuration, and operational constraints.
  - Reason: Align documentation with the implemented Flask application as the single source of truth.
