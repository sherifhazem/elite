# Central Choices Registry

Authoritative choices for cities and industries are centralized in `core/choices/registry.py` to prevent drift across routes, services, and UI layers.

## Source of Truth
- `CITIES`: الرياض, جدة, الدمام
- `INDUSTRIES`: مطاعم, تجارة إلكترونية, تعليم
- Defaults are seeded into settings storage via the admin settings service, but the registry remains the canonical declaration.

## Access Patterns
- `get_cities()` / `get_industries()` — return managed values (settings-backed, fallback to registry defaults).
- `validate_choice(value, allowed, field_name)` — shared helper returning `(is_valid, diagnostic)` while logging breadcrumbs and diagnostics into the structured logger.
- Forms consume registry-backed dropdowns through `company_registration_form`; services consume the same lists when validating payloads.

## Architecture (ASCII)
```
[Registry constants]
     |
     v
[Admin settings defaults]---->Redis (managed lists)
     |
     v
[core.choices registry]
     |           |
     |           +--> Monitoring endpoint (/dev/choices)
     v
[Forms & Services]
     |
     v
[Validation + Logging]
```

## Monitoring & Debugging
- Non-production environment exposes `/dev/choices` to inspect the active registry values.
- Validation logs include `allowed_values`, `received_value`, and `reason` whenever a choice is checked or rejected.

## Operational Notes
- No route or service should declare ad-hoc city/industry lists; always import from `core.choices`.
- Registry helpers tolerate missing settings storage during boot/tests by falling back to the baked-in defaults.
