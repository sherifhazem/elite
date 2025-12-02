# Central Choices Registry

Authoritative choices for cities and industries are centralized in `core/choices/registry.py` to prevent drift across routes, services, and UI layers.

## Source of Truth
- `CITIES`: الرياض, جدة, الدمام
- `INDUSTRIES`: مطاعم, تجارة إلكترونية, تعليم
- Admin updates mutate the in-memory registry directly so every consumer (forms, services, diagnostics) sees the same list immediately.

## Access Patterns
- `get_cities()` / `get_industries()` — return the active registry lists with graceful fallback when settings storage is unavailable.
- `validate_choice(value, allowed, field_name)` — shared helper returning `(is_valid, diagnostic)` while logging breadcrumbs and diagnostics into the structured logger.
- Forms consume registry-backed dropdowns through `company_registration_form`; services consume the same lists when validating payloads.
- Admin settings writes (`/admin/settings`) call the registry helpers to add/update/delete entries in-memory.

## Architecture (ASCII)
```
[Registry constants]
     |
     v
[Admin settings (in-memory registry mutations)]
     |
     v
[core.choices registry]
     |           |
     |           +--> Monitoring endpoints (/dev/choices, /dev/settings_status)
     v
[Forms & Services]
     |
     v
[Validation + Logging]
```

## Monitoring & Debugging
- Non-production environment exposes `/dev/choices` and `/dev/settings_status` to inspect the active registry values and list counts.
- Validation logs include `allowed_values`, `received_value`, and `reason` whenever a choice is checked or rejected.

## Operational Notes
- No route or service should declare ad-hoc city/industry lists; always import from `core.choices`.
- Registry helpers tolerate missing settings storage during boot/tests by falling back to the baked-in defaults.
- Admin settings changes are in-memory only; no database tables or migrations are required to manage dropdown values.
