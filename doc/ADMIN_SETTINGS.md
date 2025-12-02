# Admin Settings (Cities & Industries)

## Overview
The admin settings page (`/admin/settings`) is the single place to manage the registry-backed dropdown lists for **cities** and **industries**. All changes mutate the in-memory registry declared in `core/choices/registry.py`, so updates are instantly visible across forms, services, and diagnostics.

## Data Flow (ASCII)
```
[Admin UI]
   |  AJAX (add/update/delete)
   v
[Admin routes] -> [admin settings service] -> [core.choices.registry (CITIES/INDUSTRIES)]
   |                                                   |
   v                                                   v
JSON responses (no reload)                 Monitoring (/dev/settings_status)
```

## Admin Workflow
1. Open `/admin/settings` (requires `admin_required`).
2. Choose the **مدن** or **مجالات العمل** tab.
3. Add a value via the inline form (POST to `/admin/settings/add_city` or `/admin/settings/add_industry`).
4. Edit a value via the modal (POST to `/admin/settings/update_city` or `/admin/settings/update_industry`).
5. Delete a value via the inline delete button (POST to `/admin/settings/delete_city` or `/admin/settings/delete_industry`).
6. No page reload is required; the DOM refreshes from the returned JSON payloads.

## Backend Contract
- Lists are sourced from `core.choices.registry.CITIES` and `core.choices.registry.INDUSTRIES`.
- Validation rules (enforced in `app/modules/admin/services/settings_service.py`):
  - Non-empty values only.
  - No duplicates (per list).
  - Target must exist for updates/deletes.
- Logging (`app.logging.logger`): every attempt includes `admin_settings_action`, `status` (`success`/`error`), `value`, optional `reason` (`empty_value`, `duplicate_value`, `not_found`, `renamed`, etc.), and the updated `items` snapshot when successful.
- Responses are JSON only; UI uses AJAX and displays toast/error messages without redirecting.

### Routes
| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/admin/settings` | Render admin UI with current registry lists and selected tab. |
| POST | `/admin/settings/add_city` | Add a city entry. |
| POST | `/admin/settings/add_industry` | Add an industry entry. |
| POST | `/admin/settings/update_city` | Rename a city (requires `current_value` + `name`). |
| POST | `/admin/settings/update_industry` | Rename an industry (requires `current_value` + `name`). |
| POST | `/admin/settings/delete_city` | Remove a city (requires `value`). |
| POST | `/admin/settings/delete_industry` | Remove an industry (requires `value`). |
| GET | `/admin/settings/cities` | JSON snapshot of cities list (QA/automation). |
| GET | `/admin/settings/industries` | JSON snapshot of industries list (QA/automation). |

## Frontend Behavior
- Template: `app/modules/admin/templates/admin/settings.html` renders the tables and embeds JSON context for JS.
- Script: `app/modules/admin/static/admin/js/settings.js` handles add/update/delete via `fetch` calls to the endpoints above.
- Success: DOM updates instantly and a toast is shown.
- Errors: Inline alerts surface validation messages (empty/duplicate/not found) without leaving the page.

## Error Conditions
- Empty payloads → `400` with message `الاسم مطلوب.` and `reason=empty_value` (logged).
- Duplicate entries → `400` with message `العنصر موجود بالفعل.` and `reason=duplicate_value` (logged).
- Missing targets → `400` with message `لم يتم العثور على العنصر المطلوب.` and `reason=not_found` (logged).

## Development Diagnostics
- `/dev/settings_status` (non-production) returns:
```json
{
  "cities": [...],
  "industries": [...],
  "count_cities": 3,
  "count_industries": 3,
  "source": "core.choices.registry",
  "status": "ok"
}
```
- `/dev/choices` remains available for a lean registry snapshot.

## ASCII Screenshot Placeholder
```
+-------------------- Admin Settings --------------------+
| [مدن] [مجالات العمل]                                 |
| + إضافة مدينة  [جدول المدن with تعديل/حذف]           |
| + إضافة مجال  [جدول المجالات with تعديل/حذف]         |
| Toasts + inline alerts for validation                  |
+-------------------------------------------------------+
```
