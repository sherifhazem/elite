# Core Package Refactor

## Old structure
- Duplicate package existed at `/core` containing `choices/`, `cleaning/`, `normalization/`, `templates/`, `validation/`, `README.md`, and `__init__.py`.
- Application factory pointed Flask at `../core/templates` and `../core/static`, reinforcing reliance on the duplicated package path.

## New structure
- Unified core package now lives solely under `app/core/`.
- Moved modules:
  - `core/choices` → `app/core/choices`
  - `core/cleaning` → `app/core/cleaning`
  - `core/normalization` → `app/core/normalization`
  - `core/validation` → `app/core/validation`
- Templates from the deprecated package were nested inside `app/core/templates/core/templates` to avoid overwriting the existing `app/core/templates/core` set.
- Created `app/core/templates/emails/admin_broadcast.html` to match the expected email path while retaining the existing templates in `app/core/templates/core/emails/`.
- The obsolete `/core` directory was removed entirely after relocation.

## Import updates
- All imports that referenced `from core...` now target `from app.core...` in admin routes/services, company registration form/service, logging middleware, and the relocated cleaning/validation modules.
- Future modules should import shared functionality via `app.core.<module>` to align with the canonical package.

## Template path corrections
- Flask application factory now uses `template_folder="core/templates"` and `static_folder="core/static"`, pointing at the canonical paths beneath `app/`.
- Email templates can be resolved from `app/core/templates/emails/` in addition to the existing `app/core/templates/core` collection.

## Why `/core` was removed
- The top-level `/core` duplicated the official package in `app/core`, causing conflicting imports and template resolution. Consolidating under `app/core` eliminates ambiguity and ensures a single source of truth.

## How Flask resolves templates now
- Default Jinja loader resolves from `app/core/templates` (set via `template_folder`).
- Additional module template roots are still layered in `ChoiceLoader` order, preserving module-specific templates.

## How services should import modules
- Use fully qualified paths like `from app.core.choices import ...` or `from app.core.validation.validator import validate`.
- Avoid referencing removed `/core` paths to prevent `ModuleNotFoundError` and to keep registry-driven choices consistent.

## Impact on normalization, validation, and logging pipeline
- URL normalization utilities now live under `app.core.normalization`, and cleaning/validation modules referenced by the logging middleware align with the unified package.
- Central logging middleware continues to build cleaned and validated payloads using the consolidated modules, ensuring consistent diagnostics.
