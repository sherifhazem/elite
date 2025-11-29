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
- **Files:** Central logic under `core/observability/` (logger, middleware, utilities, frontend handlers) with request hooks wired in `app/__init__.py`.
- **How it works:** A middleware issues a `request_id` for every request, records start/end/duration events, and injects the ID into responses. Service functions log structured events via the shared logger. Frontend scripts add global error listeners, a traced `fetch` wrapper, and UI event logging targeting new endpoints.
- **Error tracking:** Browser errors post to `/log/frontend-error`; API traces post to `/log/api-trace`; UI interactions post to `/log/ui-event`. All payloads are captured with the `request_id` and standardized schema.
- **Log storage:** Plain-text JSON files are created under `/logs/` (`backend.log.json`, `backend-error.log.json`, `frontend-errors.log.json`, `frontend-api.log.json`, `ui-events.log.json`).

## Database and migrations
Database configuration remains unchanged. No migrations were created as part of this restructuring.
