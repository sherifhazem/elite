
# Modules Guide — ELITE Project

## 1. Purpose of This Document
This document describes each business module in the ELITE project in a clear, AI-friendly and non-ambiguous way.

AI agents must use this guide to:
- Understand the purpose and boundaries of each module.
- Write new features strictly inside the correct module.
- Avoid cross-module dependencies.
- Place new routes, templates, services, and static files in the right locations.
- Update this guide whenever the module structure changes.

---

# 2. Overview of Business Modules

The ELITE system is composed of **three primary business modules**:

1. `admin`  
2. `companies`  
3. `members`

Each module is a self-contained business domain and must remain isolated from the others.

Every module follows the same directory structure:

app/modules/<module_name>/ routes/ templates/<module_name>/ static/<module_name>/ services/ forms/ (optional)

The `admin`, `companies`, and `members` modules now strictly follow this structure; keep new files inside their module folders only.

Modules must **never** import logic or assets from each other.

---

# 3. Module: Admin

## 3.1 Purpose
The `admin` module manages the entire platform and serves as the control center.

Primary responsibilities include:
- إدارة الشركات والأعضاء  
- إدارة الخصومات  
- إدارة المحتوى  
- إدارة لوحة التحكم  
- الإشراف الكامل على النظام  

The admin module interacts with the database but does not directly communicate with other modules.

---

## 3.2 Folder Structure

app/modules/admin/ routes/ templates/admin/ static/admin/ services/ forms/

### Routes Responsibilities
- Admin dashboard  
- Management pages  
- Administrative CRUD operations  

Routes must remain thin and call services for business logic.

### Services Responsibilities
- Fetching aggregates  
- Validation  
- CRUD logic  
- Admin-specific business rules  

### Templates Responsibilities
- Dashboard UI  
- Admin-specific pages (panels, tables, forms)

### Static Responsibilities
- Admin-only CSS/JS  
- No cross-module static imports allowed  

---

# 4. Module: Companies

## 4.1 Purpose
The `companies` module manages:

- تسجيل الشركات  
- إدارة العروض  
- متابعة عمليات الاسترداد (Redemption)  
- واجهة الشركات الداخلية  

This module represents the company-side functionality of the ELITE ecosystem.

---

## 4.2 Folder Structure

app/modules/companies/ routes/ templates/companies/ static/companies/ services/ forms/

### Routes Responsibilities
- Company dashboard  
- Create/update offers  
- View performance  
- Manage redemptions  

### Services Responsibilities
- Offer logic  
- Validation rules  
- Redemption logic  
- Database queries  
- Business workflows  

### Templates Responsibilities
- صفحات إدارة الشركة  
- صفحات إضافة وعرض العروض  

### Static Responsibilities
- JS/CSS الخاص بالشركات فقط  

---

# 5. Module: Members

## 5.1 Purpose
The `members` module represents the customer-facing side of the system.

Responsibilities include:
- تسجيل الأعضاء  
- عرض الخصومات المتاحة  
- الاستفادة من العروض (Redemption)  
- إدارة البيانات الشخصية  

---

## 5.2 Folder Structure

app/modules/members/ routes/ templates/members/ static/members/ services/ forms/

### Routes Responsibilities
- Member dashboard  
- Account management  
- Offer browsing  
- Redemption actions  

### Services Responsibilities
- حساب الأعضاء  
- قواعد الاسترداد  
- منطق تسجيل الحساب  
- الربط بين العضو والعروض  

### Templates Responsibilities
- صفحات العضو الرئيسية  
- صفحات الحساب الشخصي  
- صفحات استعراض الخصومات  

### Static Responsibilities
- ملفات CSS/JS الخاصة بالأعضاء فقط  

---

# 6. Module Boundaries (Critical Rule Set)

AI agents **must follow these rules without exception**:

### ❌ Forbidden:
- No module may import code from another module.
- No template may use another module’s template folder.
- No static asset may be shared across modules.
- No service may depend on another module’s service.
- No business logic inside routes.
- No global or cross-module utility inside module folders.

### ✔ Allowed:
- Shared utilities may only exist inside:

app/core/utils/

- Shared templates (layout, header, footer) may only exist inside:

app/core/templates/

- Shared static assets (logo, base CSS) may only exist inside:

app/core/static/

---

# 7. How AI Agents Must Add or Modify Module Functionality

When implementing new features inside a module:

### Step 1 — Identify the correct module  
Admin? Company? Member?

### Step 2 — Add or modify files **inside that module only**

### Step 3 — Maintain the folder structure:
- New routes → `routes/`
- New business logic → `services/`
- New templates → `templates/<module>/`
- New CSS/JS → `static/<module>/`
- New forms → `forms/`

### Step 4 — Never place cross-module code  
If you must share logic → move it to `core/utils/`

### Step 5 — After finishing:
- Update `CHANGELOG.md`
- Update this file if a structure change occurred

---

# 8. Module Interaction Rules

Modules do NOT communicate directly.

All interactions happen via:
- Shared models  
- Route-level requests  
- Database relations  

Modules must never call each other's services or routes internally.

This rule prevents tight coupling and complexity.

---

# 9. Current Status of Modules (As of Last Update)

### Admin
- Routes and templates mostly functional  
- Services need expansion and cleanup  
- Good separation but needs consistency pass  

### Companies
- Several routes implemented  
- Some logic still inside routes (to be moved to services)  
- Module boundaries mostly correct  

### Members
- Core member flows implemented  
- Needs service cleanup  
- Routes need to be slimmed down  

---

# 10. Future Improvements

Planned enhancements:
- Full migration of business logic into service layer  
- Cleanup of routes to follow best practices  
- Strengthening module isolation  
- Documentation-driven module development  
- Simple centralized observability for all modules  

---

# 11. Summary

Each module in ELITE is a complete, isolated business domain.  
Maintaining this modular structure ensures:

- clarity  
- stability  
- scalability  
- AI-friendly development  
- low bug probability  
- predictable future expansion  

AI agents must follow this document when working inside modules  
and must update the documentation whenever changes occur.
