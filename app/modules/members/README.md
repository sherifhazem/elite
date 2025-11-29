# Members Module

- **Routes:** `app/modules/members/routes/` covers the main landing routes, member portal, offers API, user API, notifications API, and redemption API.
- **Auth:** `app/modules/members/auth/` blueprint for authentication flows.
- **Services:** `app/modules/members/services/` includes role checks, notification handling, and redemption helpers.
- **Templates:** `app/modules/members/templates/` contains member, portal, auth, and email templates.
- **Static:** `app/modules/members/static/` holds member-facing CSS, JS, images, and QR code storage.

Portal and auth blueprints now declare their own template and static folders to keep assets fully module-scoped.

## Observability Layer (Local Monitoring System)
- Member-facing services (roles, notifications, redemptions) log standardized JSON events for validation, DB actions, and completion checkpoints through the central observability logger.
- Global frontend listeners capture errors, traced API calls, and UI interactions in `main.js` and `login.js`, sending payloads to `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` with the active `request_id`.
- Request IDs are issued by middleware and returned via `X-Request-ID` so backend and browser logs in `/logs/` can be correlated locally.
