# Admin Module

- **Routes:** `app/modules/admin/routes/` (dashboard, users, offers, settings, communications, logs, notifications, reports).
- **Services:** `app/modules/admin/services/` for analytics, settings, and role-permission helpers.
- **Templates:** `app/modules/admin/templates/` scoped to the admin dashboard experience.
- **Static:** `app/modules/admin/static/` (CSS/JS for admin and reports).

The admin blueprint is defined in `app/modules/admin/__init__.py` with its own template and static roots. Logging hooks will be added later as part of the services layer.

## Observability Layer (Local Monitoring System)
- Admin services now log standardized events (`service_start`, `db_query`, `service_complete`, and soft failures) through `core/observability/logger.py`, inheriting the request-bound `request_id` from middleware.
- The reports dashboard JavaScript includes global error handling, traced `fetch` calls, and UI event logging that post to `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` for local analysis.
- Backend and frontend logs are stored as JSON lines under `/logs/`, including `backend.log.json`, `backend-error.log.json`, `frontend-errors.log.json`, `frontend-api.log.json`, and `ui-events.log.json`.
