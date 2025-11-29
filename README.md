# ELITE Modular Flask Application

This repository organizes the ELITE platform into three isolated modules (`admin`, `companies`, `members`) with a shared `core` area for cross-cutting assets.

## Module layout
- `app/modules/admin/` — dashboard blueprint, admin services, admin-only templates, and static assets.
- `app/modules/companies/` — company portal blueprint, company API blueprint, module services, templates, and static assets.
- `app/modules/members/` — authentication, member portal, public APIs, module services, templates, and static assets.
- `core/` — shared configuration placeholders plus optional shared templates or static assets.

## Running the app
```bash
export FLASK_APP=run.py
flask run
```

## Central Observability
- **Goal:** Provide a simple, centralized request tracker without touching individual routes or services.
- **Logger:** `app/core/central_logger.py` defines a single JSON logger that writes to `/logs/app.log.json` with `timestamp`, `level`, `module`, `path`, `request_id`, and `message` fields.
- **Middleware:** `app/core/central_middleware.py` generates `request_id` values, records request start/end events, captures unexpected errors, and injects the `request_id` into response headers and Flask's `g` context.
- **Automatic coverage:** The middleware is activated in `app/__init__.py` via `before_request`, `after_request`, and error handlers so every request is logged automatically.
- **Log storage:** Structured logs are stored on disk at `/logs/app.log.json`—no migrations or extra setup needed.
- **Central-only:** No routes, services, or modules need to import the logger; all observability flows through the centralized middleware layer.

## Database initialization and circular import fix
- **Issue:** The SQLAlchemy instance was created inside `app/__init__.py` and imported directly by models and routes. This caused circular imports whenever the application factory pulled in models while they simultaneously imported `db` from the app package.
- **Solution:** A dedicated database module now lives at `app/core/database.py` and exposes a single shared `db = SQLAlchemy()` instance. The application factory binds it with `db.init_app(app)` so the database is only activated inside `create_app()`.
- **Correct imports:** Use `from app.core.database import db` in models, routes, services, and utilities. Do not import `db` from `app` or construct `SQLAlchemy(app)` directly.
- **Factory usage:** Initialize the application with `create_app()` (as shown in `run.py` and the tooling scripts) so extensions, blueprints, Redis, Celery, and Mail are configured in one place.
