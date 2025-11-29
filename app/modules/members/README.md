# Members Module

- **Routes:** `app/modules/members/routes/` covers the main landing routes, member portal, offers API, user API, notifications API, and redemption API.
- **Auth:** `app/modules/members/auth/` blueprint for authentication flows.
- **Services:** `app/modules/members/services/` includes role checks, notification handling, and redemption helpers.
- **Templates:** `app/modules/members/templates/` contains member, portal, auth, and email templates.
- **Static:** `app/modules/members/static/` holds member-facing CSS, JS, images, and QR code storage.

Portal and auth blueprints now declare their own template and static folders to keep assets fully module-scoped.
<<<<<<< HEAD

## Observability Layer (Local Monitoring System)
- Member-facing services (roles, notifications, redemptions) log standardized JSON events using `log_service_start`, `log_service_step`, `log_service_error`, and `log_service_success`, inheriting the shared `X-Request-ID` header from middleware.
- Global frontend listeners in `main.js` and `login.js` rely on the traced API wrapper, UI event logger, and error handler, sending payloads to the app-level `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` endpoints.
- Request IDs are issued by middleware and returned via `X-Request-ID` so backend and browser logs in `/logs/` can be correlated locally.
=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))
