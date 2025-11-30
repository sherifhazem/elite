# ELITE — Project Overview

## 1. Purpose of This Document
This document provides a clear high-level overview of the ELITE project.  
It is intentionally written to serve as a **single source of truth** for AI agents working on the repository.

Any AI system reading this file must:
- Understand the project's purpose, direction, and boundaries.
- Respect the architectural rules described here and in the other documentation files.
- Avoid assumptions or hallucinations.
- Follow the defined structure and update documentation when changes are made.

---

## 2. Project Purpose
**ELITE** هو برنامج خصومات عضوية مبني على الويب، يوفّر عروضًا حصرية للأعضاء من خلال شراكة مع الشركات المسجّلة داخل النظام.

الفكرة الأساسية:
- الشركات تقوم بالتسجيل لتقديم خصومات حصرية لجذب عملاء جدد.
- العملاء يقومون بالتسجيل للحصول على عضوية تمنحهم الخصومات.
- النظام يسهّل عرض الخصومات، إدارتها، تتبّع عمليات الاسترداد (Redemption)، وربط الشركات بالأعضاء.

---

## 3. Current State of the Project
حتى آخر تحديث، المشروع يحتوي على:

### 3.1 Modular Application Structure
The system follows a **modular design**, with three main business modules:

- `admin` — إدارة النظام والمحتوى.
- `companies` — الشركات التي تقدم الخصومات.
- `members` — الأعضاء المستفيدون من الخصومات.

Each module contains:
- Routes  
- Templates  
- Static files  
- Business logic (partially completed and being refined)

### 3.2 Core Layer
The project includes a central `core` layer responsible for:
- Application initialization  
- Configuration logic  
- Simple centralized logging (still evolving)
- Database initialization  
- Shared templates and static assets

### 3.3 Routing and Templates
The routing works but still requires refinement to fully match the modular vision  
(i.e., moving more business logic into services and improving role separation).

### 3.4 Design Layer
- UI design is established using a predefined color palette and logo.
- This design **must not be altered** unless explicitly stated in future tasks.

### 3.5 Observability System (Current State)
A complex distributed logging layer was started but later reversed.  
The new direction is:

➡️ **Create a simple, centralized, non-intrusive logging system activated only from `__init__.py`**  
without modifying every route or service file.

This will be implemented in a future task.

---

## 4. Future Direction (Roadmap)
The project will proceed toward the following goals:

### 4.1 Achieve a Clean Modular Architecture
- Each module fully isolated (routes, services, static, templates)
- Minimal cross-module dependencies
- Clear folder boundaries

### 4.2 Centralized Simplicity Over Distributed Complexity
- No logging or tracking logic scattered across files
- One activation point at `app/__init__.py`
- A simple logs folder containing structured JSON logs

### 4.3 Service Layer Completion
- Full separation of business logic from routes
- Clear service responsibilities
- Reduced duplication

### 4.4 Documentation-Driven Development
Every task carried out by an AI agent must:
- Follow the documentation rules
- Update related .md files
- Never introduce new architectural patterns without explicit instruction
- Never create undocumented changes

### 4.5 Stability and Maintainability
- Avoid circular imports  
- Avoid deep coupling  
- Avoid unnecessary abstractions  
- Keep the code readable and consistent  

---

## 5. System Boundaries (What the Project Is NOT)
The following points define **clear boundaries** to prevent AI models from making incorrect assumptions:

- The project is **not** a marketplace.  
- The project is **not** a social network.  
- The project is **not** a CRM or analytics platform.  
- The project does **not** include machine learning, recommendation engines, or dynamic personalization.  
- The project does **not** support plugin systems or custom extensions.

AI agents must not propose features outside the system boundaries unless explicitly requested.

---

## 6. Guidance for AI Agents
If you (the AI agent) need to modify or add code:

1. **Read all files inside `/docs/` before performing any change.**  
2. Follow the architecture rules described in these documents.  
3. Respect the folder structure — do not place files in random paths.  
4. After implementing a change:
   - Update `CHANGELOG.md`
   - Update any related documentation file
5. Never create migrations, binaries, or compiled assets unless explicitly stated.  
6. If something is unclear, ask for clarification instead of assuming.

---

## 7. Summary
ELITE هو مشروع إدارة خصومات عضوية يعتمد على هندسة منظمة وقابلة للتوسع.  
الهدف هو بناء منصة متينة، واضحة، سهلة الصيانة، وتعمل وفق أسلوب تطوير صديق للوكلاء الذكيين، مع التزام تام بالبساطة، التنظيم، والتوثيق.

هذا الملف هو نقطة البداية لفهم المشروع.  
الملفات الأخرى داخل `/docs/` ستفصّل المعمارية والقواعد بدقة أكبر.

