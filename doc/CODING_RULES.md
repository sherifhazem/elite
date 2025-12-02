
# Coding Rules — ELITE Project

## 1. Purpose of This Document
This document defines strict and unambiguous coding rules for the ELITE project.

It exists to ensure that:
- All AI agents produce consistent, predictable code.
- No assumptions or hallucinations occur.
- The project structure stays aligned with the architecture.
- All new changes follow a uniform style and approach.
- Documentation is always updated correctly.

These rules are **mandatory** for any agent generating or modifying code.

---

# 2. General Python Guidelines

### 2.1 Code Readability
- Use clear, descriptive names.
- Avoid abbreviations except `db`, `id`, `req`, `res`.
- Keep functions short and focused.

### 2.2 Imports Rules
- Standard library → first group  
- Third-party libraries → second group  
- Application imports → last group  
- No wildcard imports ever (`from x import *`).

### 2.3 Forbidden Patterns
- No global variables inside modules.
- No circular imports.
- No logic inside `__init__.py` except registrations.
- No business logic inside routes.

### 2.4 Documentation
Every function with meaningful logic must include:
- A short docstring explaining purpose and parameters.

---

# 3. Rules for Routes (Blueprints)

Routes must be:
- Thin
- Declarative
- Free of business logic

### 3.1 Allowed in Routes
- Getting request data
- Calling services
- Returning responses
- Simple permission checks

### 3.2 Forbidden in Routes
❌ Database queries  
❌ Business rules  
❌ Calculations  
❌ Multi-step workflows  
❌ Modifying data directly  

### 3.3 Routes Folder Structure
Each module must have:

app/modules/<module>/routes/ <feature>_routes.py

No shared routing logic unless inside `core` and explicitly marked as generic.

---

# 4. Rules for Services

Services are the **only layer allowed** to contain business logic.

### 4.1 Responsibilities
- Input validation  
- Database interactions  
- Business rules  
- Domain workflows  
- Error handling  
- Returning structured results to routes  

### 4.2 Folder Structure

app/modules/<module>/services/ <feature>_service.py

### 4.3 Naming
- Functions must describe actual actions such as:
  - `create_offer()`
  - `validate_member_data()`
  - `redeem_discount()`

### 4.4 Forbidden in Services
❌ Rendering templates  
❌ Registering routes  
❌ Importing other modules' services  
❌ Modifying global state  
❌ Using logic from another module  

---

# 5. Rules for Templates

### 5.1 Location
Templates must be placed here:

app/modules/<module>/templates/<module>/

Shared layouts must be placed in:

app/core/templates/

### 5.2 Rules
- UI code must not contain business logic.
- Logic allowed:
  - Conditional rendering  
  - Simple loops  
  - Displaying data only  
- Do not write JS logic inside templates unless minimal.

---

# 6. Rules for Static Files

### 6.1 Location
Static files must follow module isolation:

app/modules/<module>/static/<module>/

Shared static resources:

app/core/static/

### 6.2 Forbidden
❌ Sharing static files across modules  
❌ Adding global JS logic in module folders  
❌ Writing business logic inside JS  

### 6.3 Allowed
✔ Module-specific styling  
✔ Module-specific UI behavior  

---

# 7. Rules for Models

### 7.1 Mandatory Import Rule
Models must import `db` from:

from app.core.database import db

Not from `app`.

### 7.2 Rules
- Do not execute queries inside model definitions.
- Models must not import routes or services.
- Models must avoid dependencies on modules.

---

# 8. Rules for Adding New Files

### Allowed locations
- New module files → inside that module
- New shared utilities → `/app/core/utils/`
- New shared templates → `/app/core/templates/`
- New shared static files → `/app/core/static/`

### Forbidden
❌ Creating new top-level folders  
❌ Adding files inside random locations  
❌ Adding mixed-purpose files  

---

# 9. Logging, Observability, and Monitoring Rules

### 9.1 Centralized Only
- No routes call logger directly.
- No service writes to logs.
- No module implements logging logic.

### 9.2 Source of Truth
All observability logic must be inside:

app/logging/logger.py app/core/central_middleware.py

And activated **only** from:

app/__init__.py

---

# 10. Configuration Rules

- All configuration must be stored in `/app/config/`.
- No module may define configuration values locally.
- No hardcoded secrets in any file.

---

# 11. Naming Conventions Summary

### Files

<feature>_routes.py <feature>_service.py <feature>_form.py <feature>.html

- Service files **must** use the `_service.py` suffix within their module (e.g., `member_notifications_service.py`).
- Route endpoints must be descriptive and module-scoped (e.g., `company_dashboard_overview`, `member_portal_profile`).
- Template filenames must mirror the page purpose and align with the route naming (e.g., `offers_list.html`, `dashboard_overview.html`).

### Functions

verb_object()        → create_offer() validate_()         → validate_member() get_()              → get_company_data()

### Blueprints

admin_bp companies_bp members_bp

---

# 12. Documentation Responsibilities (Critical)

Any AI agent performing code modifications **must update the documentation**:

- Update `CHANGELOG.md` after every task  
- Update relevant documentation files in `/docs/`  
- Never skip documentation updates  
- Never modify structure without updating this file  
- Never introduce new patterns without explicit instruction  

---

# 13. Forbidden Actions for AI Agents

AI agents must NOT:
- Invent new folder structures  
- Create new frameworks or architectural layers  
- Suggest design changes  
- Change UI or colors  
- Add migrations  
- Generate binary files  
- Add unnecessary complexity  
- Assume missing parts or fill gaps without instruction  

---

# 14. Summary

These coding rules ensure:
- Structural consistency  
- Predictable development  
- Zero architectural drift  
- Best compatibility with AI development agents  
- Clean modular codebase  

Every contributor—human or AI—must follow these rules as binding constraints.
