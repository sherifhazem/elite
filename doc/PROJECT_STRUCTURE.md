
# Project Structure — ELITE

## 1. Purpose of This Document
This document exists to provide a clear, precise, and authoritative overview of the ELITE project's directory structure.

Any AI agent working on this repository must:
- Use this structure as the **single source of truth**.
- Never add files outside the defined hierarchy without explicit instruction.
- Keep new additions consistent with the organization shown here.
- Update this file whenever the structure changes.

---

## 2. High-Level Directory Overview

Below is the current official directory layout of the ELITE project:

ELITE/ │ ├── app/ │   ├── core/ │   │   ├── init.py │   │   ├── database.py            # Central DB instance │   │   ├── central_logger.py      # (Planned) Simple centralized logger │   │   ├── central_middleware.py  # (Planned) Request logging middleware │   │   ├── templates/             # Shared templates (layout/shared UI) │   │   ├── static/                # Shared static assets (logo, base styles) │   │   └── utils/                 # Shared helper utilities │   │ │   ├── modules/ │   │   ├── admin/ │   │   │   ├── routes/            # Admin routes (blueprint) │   │   │   ├── templates/admin/   # Admin UI pages │   │   │   ├── static/admin/      # Admin JS/CSS/Assets │   │   │   ├── services/          # Admin business logic (to be expanded) │   │   │   └── forms/             # (Optional) Admin forms │   │   │ │   │   ├── companies/ │   │   │   ├── routes/ │   │   │   ├── templates/companies/ │   │   │   ├── static/companies/ │   │   │   ├── services/ │   │   │   └── forms/ │   │   │ │   │   ├── members/ │   │   │   ├── routes/ │   │   │   ├── templates/members/ │   │   │   ├── static/members/ │   │   │   ├── services/ │   │   │   └── forms/ │   │ │   ├── models/                    # SQLAlchemy models (independent of app) │   ├── config/                    # Application configuration files │   └── init.py                # Application factory + module registration │ ├── tools/                         # Helper scripts (seeding tools, utilities) │ ├── logs/                          # (Planned) Centralized JSON logs │ ├── docs/                          # Documentation folder (current file lives here) │   ├── PROJECT_OVERVIEW.md │   ├── ARCHITECTURE_OVERVIEW.md │   ├── PROJECT_STRUCTURE.md       # (this file) │   ├── MODULES_GUIDE.md           # (planned) │   ├── CODING_RULES.md            # (planned) │   ├── OBSERVABILITY.md           # (planned) │   ├── DEVELOPER_GUIDE_FOR_AI_AGENTS.md  # (planned) │   └── CHANGELOG.md               # (planned) │ ├── run.py                         # Application entry point ├── requirements.txt └── README.md

---

## 3. Directory Responsibilities

### 3.1 `app/core/`
The foundational layer of the entire system.
Contains shared logic used by all modules.

**What goes here:**
- Database instance (`database.py`)
- Shared templates
- Shared static assets
- Utilities
- Central logging + middleware (simple & non-intrusive)

**What should NOT go here:**
- Business logic
- Module-specific logic
- Admin/Members/Companies dependencies

---

### 3.2 `app/modules/`
Each module represents a complete business domain with its own:

- Routes
- Templates
- Static files
- Services
- Forms

Modules must remain **isolated and independent**.

---

### 3.3 `app/models/`
Houses global SQLAlchemy models.

Rules:
- Cannot import from `app` to avoid circular imports
- Must import db from:

from app.core.database import db

---

### 3.4 `app/config/`
Contains environment configurations.

---

### 3.5 `tools/`
Utility scripts such as:

- Database seeding tools
- Admin creation tools
- One-time setup scripts

Not part of application runtime.

---

### 3.6 `logs/`
Will contain centralized JSON logs produced only via the logging system activated in `__init__.py`.

No module writes logs directly.

---

### 3.7 `docs/`
Master documentation folder.

All AI agents must read this directory before working on the project.

---

## 4. Allowed Future Expansions

AI agents may only add folders to the project under these rules:

1. A new module → must follow module structure exactly
2. A new shared utility → must go into `/core/utils/`
3. New documentation → must go inside `/docs/`
4. New templates → only inside correct module folder
5. New static files → only inside correct module folder

No arbitrary folder creation is allowed.

---

## 5. Forbidden Structural Changes

AI agents must NOT:

- Modify module boundaries
- Move files out of their modules
- Mix templates or static assets between modules
- Add new layers, patterns, or frameworks
- Create migrations
- Create binary files
- Introduce distributed logging

---

## 6. Guidance for AI Agents
When updating or extending the project:

1. **Follow this structure strictly.**
2. If adding new files → place them in the correct folder.
3. If updating module logic → remain inside the module boundaries.
4. If modifying structure → update this document.
5. If unsure → ask for clarification; do not assume.

---

## 7. Summary
The ELITE project uses a clean, modular, predictable folder structure designed for AI-assisted development.

This document serves as the definitive guide for all future changes to maintain consistency, stability, and clarity across the codebase.