
# SECURITY Guidelines — ELITE Project

## 1. Purpose of This Document
This document outlines the **security rules and boundaries** that must be followed  
by all AI agents and developers working on the ELITE project.

These rules ensure:
- Safe handling of user data  
- Prevention of common security vulnerabilities  
- Protection of the system’s integrity  
- Predictable and stable development  
- Zero unsafe assumptions or undocumented behavior  

This document acts as a **security contract** for the entire codebase.

---

# 2. Security Principles

1. **Do not trust user input**  
2. **Keep business logic and validation inside services**  
3. **Keep authentication and sensitive logic inside the correct module**  
4. **Never leak sensitive data into logs or templates**  
5. **Never expose internal errors to users**  
6. **Follow least-privilege access**  
7. **Never invent or presume authentication flows**  
8. **Ask for clarification if a security-related instruction is not explicit**

---

# 3. Data Handling Rules

### ✔ Allowed:
- Validate all incoming user data  
- Sanitize inputs  
- Use safe SQLAlchemy ORM operations  
- Hash sensitive values (e.g., passwords)

### ❌ Forbidden:
- Storing plaintext passwords  
- Logging user passwords, tokens, or sensitive identifiers  
- Printing sensitive data to console or logs  
- Returning raw database errors to the UI  
- Adding analytics that collects personal data  

---

# 4. Authentication & Access Control

### 4.1 Rules for Authentication
- Authentication logic must remain inside the appropriate module (e.g., `members`).  
- Password handling must follow hashing best practices.  
- Sensitive operations must be protected by role checks.

### 4.2 Role Separation
AI agents must respect role boundaries:
- Admin logic stays in `admin`  
- Company logic stays in `companies`  
- Member logic stays in `members`

No cross-role access or assumptions.

---

# 5. Input Validation Rules

All user-facing actions must be validated in the service layer.

Services must:
- Validate inputs  
- Reject malformed data  
- Enforce business constraints  

Routes must **not** perform heavy validation themselves.

---

# 6. Models Security Rules

Models must:
- Never execute business logic  
- Never expose sensitive fields directly  
- Never depend on routes or services (to avoid leaks)  
- Follow minimal and well-defined structure  

Constraints like uniqueness and non-null rules must be explicitly set.

---

# 7. Observability and Logging Security

The centralized logging system must:
- Never log passwords  
- Never log tokens  
- Never log full request bodies  
- Never log sensitive personal information  
- Never expose stack traces to users  

All logs must be JSON-only and stored locally in `/logs/app.log.json`.

Modules must **not** introduce logging of any kind.

---

# 8. Forbidden Security Violations for AI Agents

AI agents must never:

- Implement authentication flows without explicit user request  
- Introduce JWT, OAuth, 2FA, or token managers unless asked  
- Add analytics or tracking code  
- Insert cookies without instruction  
- Use external logging/monitoring tools  
- Modify session behavior without approval  
- Assume encryption methods  
- Create direct SQL queries unless required  

If the task requires security-sensitive logic:
- The agent must ask for clarification  
- And wait for explicit instructions  

---

# 9. File Permissions & Sensitive Data

The project must never contain:
- API keys  
- Secrets  
- Tokens  
- Database URIs committed in plaintext  

If such data is needed, it must be stored in:
- `.env` file (not committed)
- Or a secure environment variable system

AI agents must never generate `.env` files with real secrets.

---

# 10. Security-Driven Documentation Rules

Whenever a change affects security:
- Update this file  
- Update `CODING_RULES.md` if coding restrictions change  
- Update `PROJECT_STRUCTURE.md` if sensitive folders are added or removed  
- Update the `CHANGELOG.md` with clear security notes  

Example entry:

Security

Enforced validation on company offer creation service

Restricted log output to remove sensitive fields


---

# 11. Safe Error Handling

Routes and services must:
- Catch and handle errors gracefully  
- Never expose stack traces to the user  
- Never print system errors in templates  

Global error handling is delegated to the centralized middleware.

---

# 12. Summary

The ELITE security model is:
- Simple  
- Centralized  
- Clear  
- Minimal  
- Designed for AI-based development  

AI agents must:
- Respect all boundaries  
- Avoid security assumptions  
- Ask when in doubt  
- Follow controlled patterns  
- Keep the system predictable and safe  

This document must be updated whenever changes impact the security posture of the project.
