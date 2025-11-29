# Members Module

- **Routes:** `app/modules/members/routes/` covers the main landing routes, member portal, offers API, user API, notifications API, and redemption API.
- **Auth:** `app/modules/members/auth/` blueprint for authentication flows.
- **Services:** `app/modules/members/services/` includes role checks, notification handling, and redemption helpers.
- **Templates:** `app/modules/members/templates/` contains member, portal, auth, and email templates.
- **Static:** `app/modules/members/static/` holds member-facing CSS, JS, images, and QR code storage.

Portal and auth blueprints now declare their own template and static folders to keep assets fully module-scoped.
