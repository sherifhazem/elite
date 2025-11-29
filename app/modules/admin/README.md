# Admin Module

- **Routes:** `app/modules/admin/routes/` (dashboard, users, offers, settings, communications, logs, notifications, reports).
- **Services:** `app/modules/admin/services/` for analytics, settings, and role-permission helpers.
- **Templates:** `app/modules/admin/templates/` scoped to the admin dashboard experience.
- **Static:** `app/modules/admin/static/` (CSS/JS for admin and reports).

The admin blueprint is defined in `app/modules/admin/__init__.py` with its own template and static roots. Logging hooks will be added later as part of the services layer.
