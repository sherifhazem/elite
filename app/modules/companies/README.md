# Companies Module

- **Routes:** `app/modules/companies/routes/` includes the company portal pages plus `/api/companies` API routes.
- **Services:** `app/modules/companies/services/` contains company registration and offer helpers.
- **Forms:** `app/modules/companies/forms/module_forms/` holds the company registration form.
- **Templates:** `app/modules/companies/templates/` dedicated to company-facing pages.
- **Static:** `app/modules/companies/static/` holds company CSS and JS assets.

The company portal blueprint lives in `app/modules/companies/__init__.py` with template and static folders scoped to this module.

## Observability Layer (Local Monitoring System)
- Company services (`app/modules/companies/services/`) emit standardized JSON logs for validation, database access, and soft failures using the shared logger in `core/observability/`.
- Frontend assets now include a global error listener, traced `fetch` wrapper, and UI event logging that post to `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` with the active `request_id`.
- Request correlation is enabled via middleware, adding an `X-Request-ID` header to responses and persisting traces to `/logs/frontend-*.log.json` alongside backend service logs.
