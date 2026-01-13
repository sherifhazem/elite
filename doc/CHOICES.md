# ELITE – Managed Choices

## 1. Purpose
Managed choices provide controlled, centralized lookup values used across the platform. They replace hardcoded lists and prevent invalid or inconsistent data entry.

---

## 2. Storage Model
- Choices are stored in a dedicated database table.
- Each record includes:
  - `list_type`
  - `name`
  - Optional ordering metadata
- Uniqueness is enforced per (`list_type`, `name`).

---

## 3. Common List Types
Examples of managed lists include:
- Cities
- Industries
- Business categories
- Any admin-defined lookup data required by forms or services

---

## 4. Usage Rules
- Choices are referenced by foreign keys or validated values.
- Client input must match an existing managed choice.
- Invalid or unknown values are rejected server-side.

---

## 5. Admin Management
- Only admins can create, update, or delete choices.
- Changes take effect immediately across all dependent forms and services.
- CSRF protection applies to all management actions.

---

## 6. Enforcement
- Validation occurs at the service layer.
- Templates do not define or override available options.
- Removal of a choice in use is blocked or handled safely.

---

## 7. Extension Guidelines
- New lookup types must be registered consistently.
- Do not duplicate managed choices in code or templates.
- Use managed choices for any user-facing selectable data.
