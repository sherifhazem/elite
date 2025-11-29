# Core Shared Assets

This folder holds shared scaffolding for configuration, observability, utilities, templates, and static assets that are not tied to a single module.

Currently the module templates live under `core/templates/` and the shared static root is configured via the Flask app to `core/static/`.

## Observability Layer (Local Monitoring System)
- Core observability code lives under `core/observability/` (config, logger, middleware, frontend handlers, utils).
- Request IDs are injected via middleware in `app/__init__.py` and logged through the standardized schema for backend and frontend events.
- Local JSON logs are emitted to `/logs/` for backend (`backend*.log.json`) and frontend (`frontend-*.log.json`, `ui-events.log.json`) traces.
