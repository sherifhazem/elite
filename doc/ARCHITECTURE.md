# ELITE – System Architecture

## 1. Project Overview
ELITE is a role-based Flask web application for managing discount offers, memberships, partner portals, and administrative operations. The system is designed around strict access control, centralized business rules, and auditable actions.

---

## 2. Architectural Principles
- Role-driven access (Admin / Company / Member)
- Server-side enforcement of all business rules
- Shared services with clear module boundaries
- Audit-first design (activity logging and traceability)
- Configuration-driven behavior (admin settings, feature toggles)

---

## 3. Application Factory
- Entry point: `app.create_app`
- Responsibilities:
  - Load environment-based configuration
  - Initialize extensions (SQLAlchemy, Migrate, Login, CSRF, Mail, Celery when enabled)
  - Register blueprints
  - Register logging and request middleware
  - Enforce security constraints at startup

---

## 4. Module Structure

### Members Module (`app/modules/members`)
- Member authentication and session handling
- Member portal UI
- Offers browsing
- Redemptions creation and status tracking
- Usage-code verification
- Member notifications

### Companies Module (`app/modules/companies`)
- Company registration and completion workflow
- Company dashboard
- Offer management (CRUD)
- Redemption verification and confirmation
- Usage-code generation

### Admin Module (`app/modules/admin`)
- Admin authentication and dashboards
- User, company, and offer management
- Global settings and managed lists
- Reports and exports
- Activity log review
- Role-permission configuration

---

## 5. Service Layer
- Shared logic: `app/services`
- Module-specific services: `app/modules/*/services`
- Services encapsulate:
  - Validation
  - Eligibility rules
  - Usage limits
  - Admin-configurable behavior
- Routes delegate logic to services; no business rules in views.

---

## 6. Data Layer
- SQLAlchemy ORM models in `app/models`
- Core entities:
  - User
  - Company
  - Offer
  - Redemption
  - UsageCode
  - Notification
  - ActivityLog
  - AdminSetting
- Relationships and constraints enforce integrity at the database level.

---

## 7. Request Lifecycle
1. Request enters Flask
2. Logging middleware initializes request/trace context
3. `before_request`:
   - Resolve current user
   - Attach role and company context
   - Enforce access control
4. Route handler executes and calls services
5. `after_request`:
   - Refresh authentication cookie when applicable
   - Emit structured log entry with correlation IDs

---

## 8. Logging Architecture
- Centralized structured logging
- JSON logs written to console and `logs/app.log.json`
- Correlation identifiers:
  - Request ID
  - Trace ID
  - Parent ID
- All critical actions are traceable to user and role context.

---

## 9. Optional Infrastructure
- Redis:
  - Optional
  - Used for role-permission and admin-setting caches
  - Enabled only when `REDIS_URL` is configured
- Celery:
  - Optional
  - Used for background tasks when configured

---

## 10. Extension Boundaries
- New features must live within the appropriate module.
- Cross-cutting logic belongs in `app/services`.
- New persistent data requires explicit models and migrations.
- No module may bypass shared access-control or logging middleware.
