# ELITE Modular Flask Application

This repository now organizes the ELITE platform into three isolated modules (`admin`, `companies`, `members`) with a shared `core` area for cross-cutting assets.

## Module layout
- `app/modules/admin/` — dashboard blueprint, admin services, admin-only templates, and static assets.
- `app/modules/companies/` — company portal blueprint, company API blueprint, module services, templates, and static assets.
- `app/modules/members/` — authentication, member portal, public APIs, module services, templates, and static assets.
- `core/` — shared observability/config placeholders plus optional shared templates or static assets.

## Running the app
```bash
export FLASK_APP=run.py
flask run
```

## Notes on the restructuring
- Blueprints import paths now point to the module packages under `app/modules/`.
- Each module owns its templates and static files; shared base templates live under `core/templates/`.
- The Flask app serves shared assets from `core/static` and wires additional template loaders for each module.
- Services are grouped by module (admin, companies, members) with shared mail utilities retained in `app/services/`.

## Database and migrations
Database configuration remains unchanged. No migrations were created as part of this restructuring.
