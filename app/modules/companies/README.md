# Companies Module

- **Routes:** `app/modules/companies/routes/` includes the company portal pages plus `/api/companies` API routes.
- **Services:** `app/modules/companies/services/` contains company registration and offer helpers.
- **Forms:** `app/modules/companies/forms/module_forms/` holds the company registration form.
- **Templates:** `app/modules/companies/templates/` dedicated to company-facing pages.
- **Static:** `app/modules/companies/static/` holds company CSS and JS assets.

The company portal blueprint lives in `app/modules/companies/__init__.py` with template and static folders scoped to this module.

## Observability Layer (Local Monitoring System)
- Company services (`app/modules/companies/services/`) log through `log_service_start`, `log_service_step`, `log_service_error`, and `log_service_success`, ensuring every step is tied to the centralized `X-Request-ID` header and JSON schema.
- Frontend assets rely on the shared API wrapper, UI event logger, and global error handler, sending activity to the app-level `/log/frontend-error`, `/log/api-trace`, and `/log/ui-event` endpoints with the active request id.
- Middleware injects the request id into responses and all traces stored under `/logs/frontend-*.log.json` alongside backend service logs.
