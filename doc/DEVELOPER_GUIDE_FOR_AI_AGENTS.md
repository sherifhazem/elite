
# Developer Guide for AI Agents — ELITE Project

## 1. Purpose of This Document
This guide defines the mandatory workflow, behavior, responsibilities,  
and constraints for any AI agent working on the ELITE project.

Its goal is to ensure:
- Consistent code quality  
- Zero hallucinations  
- Zero structural drift  
- Full alignment with documentation  
- Safe incremental development  
- Predictable results  

This document acts as a **behavioral contract** for all AI-based contributions.

---

# 2. Core Principles for AI Agents

Any AI agent interacting with the project must follow these principles:

### ✔ Principle 1 — Documentation First
Before generating or modifying any code:
- Read all files in `/docs/`
- Honor architectural, structural, and coding rules exactly

### ✔ Principle 2 — Ask Before Assuming
If any requirement is unclear:
- Ask for clarification  
- Never assume  
- Never invent missing details  
- Never introduce external patterns  

### ✔ Principle 3 — Only Work Within the Requested Scope
The agent must:
- Modify only the requested files  
- Avoid touching unrelated areas  
- Avoid suggesting extra improvements unless requested  

### ✔ Principle 4 — Predictability Over Creativity
The agent must:
- Follow the established architecture  
- Avoid introducing new methodologies  
- Avoid refactorings not explicitly requested  

### ✔ Principle 5 — Maintain Documentation
After each task:
- Update `CHANGELOG.md`  
- Update any relevant doc file in `/docs/`  
- Update module docs if the structure changed  

---

# 3. Mandatory Development Workflow

Every AI agent must follow this workflow **step-by-step** for every task:

## Step 1 — Read The Documentation
- Review `PROJECT_OVERVIEW.md`  
- Review `ARCHITECTURE_OVERVIEW.md`  
- Review `PROJECT_STRUCTURE.md`  
- Review `MODULES_GUIDE.md`  
- Review `CODING_RULES.md`  
- Review `OBSERVABILITY.md`  

## Step 2 — Understand The Task Clearly
If the task is unclear:
- Ask questions  
- Request examples  
- Request clarification  

## Step 3 — Plan the Change
The agent must:
- Identify which files are affected  
- Identify which module the task belongs to  
- Ensure no cross-module violations  

## Step 4 — Generate the Code
Follow the rules strictly:
- Use correct folder  
- Use correct naming  
- Avoid forbidden patterns  
- Maintain structure  
- Keep routes thin  
- Place business logic in services  
- Never modify UI design unless requested  

## Step 5 — Validate Against Architecture
The agent must verify:
- No circular imports  
- No structure violations  
- No new files outside allowed paths  
- Observability remains centralized  
- No logging outside core  

## Step 6 — Update Documentation
The agent must:
- Update `CHANGELOG.md`  
- Update module docs if structure changed  
- Update coding rules if new conventions were approved  
- Update this guide if AI behavior rules changed  

## Step 7 — Provide Clean Output
The agent must:
- Return only the required code  
- Avoid commentary unless necessary  
- Avoid meta-analysis  
- Avoid repeating instructions  

---

# 4. Module Interaction Rules (Critical)

AI agents must follow these strict boundaries:

### ❌ Modules must NEVER import from each other
No:

admin → companies
companies → members
members → admin

### ❌ Services must NOT cross domains  
A service inside `companies` may not call a service inside `members`.

### ❌ Templates and static files must stay inside their module

### ❌ Shared logic must go in `app/core/utils/`

### ✔ Models may be shared across modules

### ✔ Routes must stay in their module only

---

# 5. Observability Rules for AI Agents

AI agents must strictly follow:

### ✔ Logging is centralized  
Only inside:

app/core/central_logger.py app/core/central_middleware.py

### ❌ No logging inside:
- modules  
- routes  
- services  
- JS  
- tools  

### ✔ Logging is activated only in:

app/init.py

Any attempt to add logging elsewhere is forbidden unless explicitly requested.

---

# 6. File Creation & Naming Rules

### ✔ Allowed locations for new files:
- Inside the correct module:

routes/ services/ templates/<module>/ static/<module>/ forms/

- Shared logic:

app/core/utils/ app/core/templates/ app/core/static/

- Docs:

docs/

### ❌ Forbidden locations:
- Top-level project folder  
- Random new folders  
- Inside unrelated modules  
- Inside `core/` unless purpose is shared  
- Any type of binary files  

### ✔ Naming rules:
- `something_routes.py`
- `something_service.py`
- `something_form.py`
- Template names describing the UI page
- JS/CSS mirror the template or component names

---

# 7. Behavior Rules When Task Is Ambiguous

If the requested task is unclear or incomplete:
- The agent must ask questions  
- Must NOT assume missing requirements  
- Must NOT invent new architecture  
- Must NOT apply optimizations unless explicitly asked  
- Must NOT create additional features  

---

# 8. Responsibilities for Updating Documentation

After any modification, the AI agent must:

### Mandatory:
- Add entry to `CHANGELOG.md`  
- Update relevant architecture docs  
- Update module docs if folders or features changed  
- Update coding rules if new naming or practices become part of the project  
- Update this guide if behavior rules change  

### Forbidden:
❌ Leaving documentation outdated  
❌ Skipping CHANGELOG updates  
❌ Making undocumented changes  

---

# 9. Forbidden Actions for AI Agents

The following actions are strictly forbidden:

- Adding migrations  
- Adding binary files  
- Altering UI design or colors  
- Creating new layers or architecture  
- Inventing new folders or file types  
- Introducing external libraries  
- Adding logging outside the core  
- Cross-module imports  
- Distributed tracking or analytics  
- Guessing requirements  
- Making structural refactors without explicit instruction  

---

# 10. How Agents Should Communicate

When replying to the user:
- Be concise  
- Be neutral  
- Avoid flattery  
- Avoid repeating the user’s instructions  
- Provide clean, actionable results  
- Avoid meta explanations  

If the user asks for clarification:
- Ask specific, direct questions  

If the user requests code:
- Provide only the required code  
- With minimal commentary  
- Following project rules exactly  

---

# 11. Summary

This document defines:
- How AI agents must behave  
- How tasks must be processed  
- How code must be generated  
- How the architecture must be respected  
- How documentation must be maintained  

Agents must treat this file as **the behavioral contract** governing their work.  
Failure to follow these rules leads to inconsistent or unsafe output.  

Any future AI agent must read this file before making any changes.
