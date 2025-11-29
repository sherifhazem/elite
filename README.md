# ELITE Modular Flask Application

This repository now organizes the ELITE platform into three isolated modules (`admin`, `companies`, `members`) with a shared `core` area for cross-cutting assets.

## Module layout
- `app/modules/admin/` — dashboard blueprint, admin services, admin-only templates, and static assets.
- `app/modules/companies/` — company portal blueprint, company API blueprint, module services, templates, and static assets.
- `app/modules/members/` — authentication, member portal, public APIs, module services, templates, and static assets.
- `core/` — shared observability/config placeholders plus optional shared templates or static assets.

## Running the app
```bash
export FLASK_APP=run.py
flask run
```

## Notes on the restructuring
- Blueprints import paths now point to the module packages under `app/modules/`.
- Each module owns its templates and static files; shared base templates live under `core/templates/`.
- The Flask app serves shared assets from `core/static` and wires additional template loaders for each module.
- Services are grouped by module (admin, companies, members) with shared mail utilities retained in `app/services/`.
- Observability, request correlation, and frontend tracing now live under `core/observability/` with plain-text JSON logs written to `/logs/`.

## Observability Layer (Local Monitoring System)
- **Goal:** Provide local-only, JSON-based logging and tracing for backend and frontend flows without external services.
- **Files:** Central logic under `core/observability/` (logger, middleware, utilities, frontend handlers, ingestion routes) with request hooks wired in `app/__init__.py`.
- **Middleware:** `init_observability` registers `before_request`/`after_request` hooks to guarantee a `request_id` for every request, measure duration, and return the ID in the configurable header (`OBSERVABILITY_CONFIG.REQUEST_ID_HEADER`, default `X-Request-ID`).
- **Config:** A dedicated `OBSERVABILITY_CONFIG` section in `app/config.py` centralizes log paths, log levels, handler options, and request-id settings; all observability utilities consume this single source of truth.
- **Service logging:** Services use the shared helpers `log_service_start`, `log_service_step`, `log_service_error`, and `log_service_success` for consistent event names and automatic `request_id` propagation.
- **Ingestion endpoints:** App-level routes under the `/log/*` blueprint accept frontend error logs, API traces, and UI events for every module, keeping middleware coverage and CSRF exemptions centralized.
- **Frontend tracing:** Browser scripts rely on the traced `fetch` wrapper, UI event logger, and global error handler; every call is sent through the `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` endpoints.
- **Log storage:** Plain-text JSON files are created under `/logs/` (`backend.log.json`, `backend-error.log.json`, `frontend-errors.log.json`, `frontend-api.log.json`, `ui-events.log.json`).

## Database initialization and circular import fix
- **Issue:** The SQLAlchemy instance was created inside `app/__init__.py` and imported directly by models and routes. This caused circular imports whenever the application factory pulled in models while they simultaneously imported `db` from the app package.
- **Solution:** A dedicated database module now lives at `app/core/database.py` and exposes a single shared `db = SQLAlchemy()` instance. The application factory binds it with `db.init_app(app)` so the database is only activated inside `create_app()`.
- **Correct imports:** Use `from app.core.database import db` in models, routes, services, and utilities. Do not import `db` from `app` or construct `SQLAlchemy(app)` directly.
- **Factory usage:** Initialize the application with `create_app()` (as shown in `run.py` and the tooling scripts) so extensions, blueprints, Redis, Celery, and Mail are configured in one place.
- **No migrations or binaries:** The change isolates initialization only; no binary artifacts or database migrations were introduced.
