
# Architecture Overview — ELITE Project

## 1. Purpose of This Document
This document defines the architectural structure of the ELITE project.  
It exists to ensure that AI agents working on this repository can:

- Understand the architecture accurately  
- Follow the existing design decisions  
- Apply changes consistently and safely  
- Avoid hallucinations or structural assumptions  
- Update the architecture documentation when needed  

This document is a binding reference for all future development.

---

## 2. High-Level Architecture Summary
ELITE is a **modular Flask web application** designed around clear boundaries between business domains.

The architecture is composed of:

1. **Application Core (`app/core/`)**  
2. **Business Modules (`app/modules/`)**  
3. **Template Layer (modular + shared)**  
4. **Static Layer (modular + shared)**  
5. **Configuration Layer**  
6. **Central Observability Layer (centralized and active)**
7. **Database + Models Layer**  

Each layer has a defined purpose and must remain consistent.

---

## 3. Application Core
Located in:

app/core/

This layer contains the global components that serve the overall application:

### Core Responsibilities
- Application initialization  
- Database initialization (via central database instance)  
- Central logging (simple, centralized system)  
- Shared templates and static assets  
- Global utilities  

### Key Characteristics
- The core layer **must not contain business logic**.  
- No module-specific imports are allowed here.  
- This layer must remain minimal, stable, and reusable.

---

## 4. Business Module Architecture
Each domain lives in a dedicated module inside:

app/modules/ /admin/ /companies/ /members/

### Module Responsibilities
Each module contains everything related to its domain:

- Routing  
- Templates  
- Static files  
- Forms (if present)  
- Local utilities  
- Services (in-progress and will be expanded)

### Module Boundaries (Very Important)
To avoid confusion for AI agents:

1. **Modules must never import each other.**  
2. **No shared logic inside modules — only in `core/` or `shared` folders.**  
3. **Each module should remain self-contained and independent.**  
4. **Routes should not contain business logic.**  
5. **Business logic belongs in services, not routes.**

---

## 5. Templates Layer
Templates are organized as:

app/modules/<module_name>/templates/<module_name>/

With a shared template folder:

app/core/templates/

### Rules for Templates:
- Shared layout elements (headers, footers, base templates) belong in `core/templates/`.
- Module-specific UI must stay inside the module folder.
- No template may reference content belonging to another module's folder.

---

## 6. Static Assets Layer
Static files follow the same structure:

app/modules/<module>/static/<module>/

Shared static resources (logo, base CSS, shared JS):

app/core/static/

### Rules:
- No module is allowed to modify another module’s static assets.
- Shared static resources must be general-purpose only.
- Module-specific CSS/JS must stay inside module folders.

---

## 7. Database + Models Layer
Models currently live inside:

app/models/

### Rules:
- Models must not import Flask `app` directly (to avoid circular imports).
- The database instance `db` must always be imported from:

from app.core.database import db

### Current Status:
- Models no longer depend on access-control services; role checks remain self-contained to avoid circular imports.

### Future Direction:
A more organized domain-oriented model structure may be introduced later, but **only with explicit instruction**.

---

## 8. Observability Layer (Centralized Approach)
The project uses a minimal, centralized observability system.

### Centralized Logging Only
- Activated from `app/__init__.py` via `initialize_logging(app)` and the central middleware hooks.
- No logging code inside modules (routes/services).
- Central logger defined in `app/logging/logger.py` that writes JSON to `logs/app.log.json` with daily rotation (4-day retention).
- Request middleware in `app/core/central_middleware.py` handles request start/end timing and unhandled errors.
- No distributed instrumentation in JS or Python.

### Observability Responsibilities:
- Log basic request lifecycle with `request_id`, path, method, and duration.
- Log unhandled errors and return the `request_id` in error responses.
- Provide a clean and minimal log format.
- Never interfere with business modules.

---

## 9. Configuration Layer
Project configuration lives in:

app/config/

Rules:
- Configuration must be environment-aware (dev/prod).
- Modules should not store configuration.
- Observability configuration must also reside here once finalized.

---

## 10. Routing Architecture
Routes must follow these principles:

- Each module defines its own Blueprint.  
- No module may register a route for another module.  
- Business logic must not be embedded inside routes.  
- Routes should be clean, thin, and call services only.  

---

## 11. Future Architectural Goals
These objectives define where the architecture is moving:

### 11.1 Complete Service Layer Migration
- Move business logic from routes → services
- Standardize naming conventions
- Ensure testability and clarity

### 11.2 Strict Boundaries
- Modules remain isolated
- Shared logic goes to `core/` only

### 11.3 Centralized Observability
- No propagation of logging code  
- One activation point  
- Zero intrusion into module code  

### 11.4 Full Documentation-Driven Development
- Every structural change must update documentation  
- AI agents must rely on docs to avoid structural drift  

---

## 12. Guidance for AI Agents (Critical Section)
Any AI agent modifying the project must:

1. Read all documentation under `/docs/` before making changes.  
2. Respect module boundaries.  
3. Avoid guessing or introducing new patterns.  
4. Follow the architecture rules as absolute constraints.  
5. Update:
   - `CHANGELOG.md`  
   - and any relevant architecture file  
   when modifications are made.  
6. Ask for clarification if something is ambiguous.  
7. Never add migrations or binary files.  
8. Never modify UI design or colors without explicit instruction.  

---

## 13. Summary
The ELITE architecture is modular, structured, and built with clarity in mind.  
This document must serve as the architectural contract for all current and future development.

Any structural change must be reflected here to maintain a consistent and predictable codebase.
