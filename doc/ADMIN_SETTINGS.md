# ELITE – Admin Settings

## 1. Purpose
Admin settings provide a centralized, database-driven mechanism for controlling platform behavior without modifying application code. All settings are enforced server-side.

---

## 2. Storage Model
- Admin settings are stored in the `AdminSetting` model.
- Each setting consists of:
  - `key`
  - `value` (JSON-serializable)
  - Timestamps for auditing
- Settings are loaded at runtime and cached when applicable.

---

## 3. Setting Categories

### Activity Rules
Control how member and partner activity is evaluated.

- **Member activity rules**
  - Required usage count
  - Time window (days)
  - Grace-mode handling

- **Partner activity rules**
  - Required usage count
  - Unique customer requirement
  - Time window (days)
  - Grace-mode handling

---

### Usage-Code Configuration
Controls verification behavior for usage codes.

- Configurable attributes:
  - Code format (stored)
  - Expiry duration (seconds)
  - Per-window usage limits
- Verification logic enforces numeric-only codes despite stored format options.

---

### Offer Type Toggles
Enable or disable offer classifications globally.

- Examples:
  - First-time offers
  - Loyalty offers
  - Active-members-only offers
  - Time-based offers
- Disabled types cannot be selected or saved in offers.

---

### Managed Lists
Admin-managed lookup data used across the platform.

- Examples:
  - Cities
  - Industries
- Stored centrally and referenced by foreign keys.

---

## 4. Access Control
- Admin settings are accessible only to:
  - `admin`
  - `superadmin`
- Changes are protected by CSRF and role checks.

---

## 5. Enforcement Rules
- Settings are enforced at service level, not in templates.
- Invalid or missing settings fallback to safe defaults.
- No client-side override is allowed.

---

## 6. Auditing
- Changes to admin settings are logged.
- Related actions may emit entries to `ActivityLog`.
- Historical values are not exposed through the UI.

---

## 7. Extension Guidelines
- New settings must:
  - Have a clear scope
  - Be validated on read
  - Default to restrictive behavior
- Settings must not introduce conditional security bypasses.
