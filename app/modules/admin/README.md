# Admin Module

- **Routes:** `app/modules/admin/routes/` (dashboard, users, offers, settings, communications, logs, notifications, reports).
- **Services:** `app/modules/admin/services/` for analytics, settings, and role-permission helpers.
- **Templates:** `app/modules/admin/templates/` scoped to the admin dashboard experience.
- **Static:** `app/modules/admin/static/` (CSS/JS for admin and reports).

The admin blueprint is defined in `app/modules/admin/__init__.py` with its own template and static roots. Logging hooks will be added later as part of the services layer.
<<<<<<< HEAD

## Observability Layer (Local Monitoring System)
- Admin services emit structured events with `log_service_start`, `log_service_step`, `log_service_error`, and `log_service_success`, all funneled through the central logger and the shared request `X-Request-ID` header.
- The reports dashboard JavaScript now relies on the global API wrapper and UI logger; all API calls, UI events, and JS errors are posted to the app-level `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` endpoints.
- Backend and frontend logs are stored as JSON lines under `/logs/`, including `backend.log.json`, `backend-error.log.json`, `frontend-errors.log.json`, `frontend-api.log.json`, and `ui-events.log.json`.
=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))
