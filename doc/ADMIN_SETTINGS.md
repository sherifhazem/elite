# Admin Settings (Cities, Industries & Membership Discounts)

## Overview
The admin settings page (`/admin/settings`) is the single place to manage the registry-backed dropdown lists for **cities**, **industries**, and the centrally managed **membership discount matrix**. All changes mutate the in-memory registry declared in `core/choices/registry.py` (for dropdowns) or the database-backed membership discount list, so updates are instantly visible across forms, services, and diagnostics.

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

Membership Discounts flow:

```
[Admin UI (membership tab)]
   |   AJAX (save)
   v
[Admin settings route] -> [settings_service.save_list("membership_discounts", payload)]
                                     |
                                     v
[Offer/User logic fetches discounts at runtime]
```

## Admin Workflow (Cities & Industries)
1. Open `/admin/settings` (requires `admin_required`).
2. Choose the **مدن** or **مجالات العمل** tab.
3. Add a value via the inline form (POST to `/admin/settings/add_city` or `/admin/settings/add_industry`).
4. Edit a value via the modal (POST to `/admin/settings/update_city` or `/admin/settings/update_industry`).
5. Delete a value via the inline delete button (POST to `/admin/settings/delete_city` or `/admin/settings/delete_industry`).
6. No page reload is required; the DOM refreshes from the returned JSON payloads.

## Backend Contract
- Lists are sourced from `core.choices.registry.CITIES` and `core.choices.registry.INDUSTRIES`.
- Membership discounts are stored in `LookupChoice` rows with `list_type="membership_discounts"` and a JSON `name` payload of `{ "membership_level": "Basic", "discount_percentage": 10 }`.
- Validation rules (enforced in `app/modules/admin/services/settings_service.py`):
  - Non-empty values only for lists.
  - No duplicates (per list) and one discount per membership level.
  - Target must exist for updates/deletes.
  - Membership level must be in `User.MEMBERSHIP_LEVELS`.
  - Discount must be numeric between 0 and 100.
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
| POST | `/admin/settings/save` | Persist membership discount percentages (AJAX only). |

> Membership discounts reuse the existing service layer via `settings_service.save_list("membership_discounts", payload)`.

## Frontend Behavior
- Template: `app/modules/admin/templates/admin/settings.html` renders the tables and embeds JSON context for JS.
- Script: `app/modules/admin/static/admin/js/settings.js` handles add/update/delete via `fetch` calls to the endpoints above.
- Success: DOM updates instantly and a toast is shown.
- Errors: Inline alerts surface validation messages (empty/duplicate/not found) without leaving the page.

## Membership Discounts UI
- Open the **خصومات العضوية** tab inside `/admin/settings` to view every membership level and its configured percentage.
- Edit the numeric percentage (0–100) inline; membership level labels are read-only.
- Click **حفظ الخصومات** to persist changes via AJAX (`/admin/settings/save`).
- Validation errors (non-numeric or out-of-range) appear directly under the input; success shows the standard toast.
- Saved values refresh immediately from the backend response—no page reload required.

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
  "membership_discounts": [
    {"membership_level": "Basic", "discount_percentage": 0}
  ],
  "count_cities": 3,
  "count_industries": 3,
  "count_membership_discounts": 4,
  "source": "core.choices.registry",
  "status": "ok"
}
```
- `/dev/choices` remains available for a lean registry snapshot.

## ASCII Screenshot Placeholder
```
+-------------------- Admin Settings --------------------+
| [مدن] [مجالات العمل] [خصومات العضوية]                |
| + إضافة مدينة  [جدول المدن with تعديل/حذف]           |
| + إضافة مجال  [جدول المجالات with تعديل/حذف]         |
| [جدول الخصومات: مستوى، نسبة مئوية قابلة للتعديل]     |
| حفظ الخصومات ⇢ Toasts + inline alerts                 |
+-------------------------------------------------------+
```
