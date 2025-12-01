
# CHANGELOG — ELITE Project

This file documents all notable changes to the ELITE project.  
Every update, by humans or AI agents, **must** be recorded here.

The format follows simple, AI-friendly rules to maintain consistency and clarity.

---

# ❗ Mandatory Rules for Writing Changelog Entries

Any time an AI agent or developer modifies the project, they must:

### ✔ 1. Add a new entry under the correct version  
### ✔ 2. Write short, clear bullet points  
### ✔ 3. Mention affected modules/files  
### ✔ 4. Document structural changes precisely  
### ✔ 5. Reference documentation updates (if done)  
### ✔ 6. Never skip adding an entry  
### ✔ 7. Never modify an older entry  

---

# 🧩 Changelog Entry Format

Use this template for each new update:

[Version Number] - YYYY-MM-DD

Added

New features or new files.


Changed

Updated or refactored existing features.


Fixed

Bug fixes or behavioral corrections.


Removed

Deleted features or deprecated components.


Documentation

Files in /docs/ that were updated.


If a section is empty, include it with a placeholder (`- None`).

---

# 📌 Current Versioning Strategy

The project uses **manual semantic versioning**:

- **MAJOR**: Breaking structural changes  
- **MINOR**: New features or new modules  
- **PATCH**: Fixes and small adjustments  

Initial version after documentation restructuring:

v0.1.0 — Documentation Baseline Version

---

# 📝 Changelog History

---

## v0.1.0 — 2025-01-01
### Added
- Added `/docs/PROJECT_OVERVIEW.md`
- Added `/docs/ARCHITECTURE_OVERVIEW.md`
- Added `/docs/PROJECT_STRUCTURE.md`
- Added `/docs/MODULES_GUIDE.md`
- Added `/docs/CODING_RULES.md`
- Added `/docs/OBSERVABILITY.md`
- Added `/docs/DEVELOPER_GUIDE_FOR_AI_AGENTS.md`
- Added `/docs/CHANGELOG.md` (this file)

### Changed
- None

### Fixed
- None

### Removed
- None

### Documentation
- Established the full documentation suite for AI-driven development workflow.

---

# ✔ Future Entries Will Be Added Below

All future changes must append new entries following the same structure.

## v0.1.1 — 2025-12-01
### Added
- Added admin dashboard and company management service layers to host business logic.

### Changed
- Refactored admin dashboard routes to rely on services for logout handling and metrics preparation.
- Slimmed admin company routes by delegating CRUD operations and status transitions to services.

### Fixed
- None

### Removed
- None

### Documentation
- None

## v0.1.3 — 2025-12-03
### Added
- None

### Changed
- Reorganized admin, companies, and members module assets under module-named templates and static directories to align with the official layout.
- Simplified companies form imports by moving the company registration form to the module forms root.

### Fixed
- Removed duplicate and deprecated module files that were outside the approved structure.

### Removed
- Legacy helper and placeholder files no longer needed after the module reorganization.

### Documentation
- Updated structure documentation to reflect the cleaned module directories.

## v0.1.2 — 2025-12-02
### Added
- None

### Changed
- Standardized model imports across services and routes to use the central `app.models` aggregator for consistency.
- Moved access-control resolution inside `create_app` to defer optional dependencies until after app creation.

### Fixed
- Eliminated the User model dependency on access-control services by embedding the role access matrix locally.

### Removed
- None

### Documentation
- Updated architecture notes to reflect the self-contained model role checks.

## v0.1.4 — 2025-12-01
### Added
- Introduced a shared base layout under `app/core/templates/core/` for member-facing public views.

### Changed
- Relocated email templates to `app/core/templates/core/emails/` and updated all render paths to the shared location.

### Fixed
- Pointed member templates to the shared base layout to align with the standardized template loader.

### Removed
- None

### Documentation
- Updated `PROJECT_STRUCTURE.md` and `MODULES_GUIDE.md` to reflect the shared template locations.
