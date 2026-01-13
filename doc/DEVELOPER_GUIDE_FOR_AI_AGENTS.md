# ELITE – Developer Guide for AI Agents

## 1. Purpose
This document defines strict operational rules for any AI agent interacting with the ELITE codebase. The goal is to preserve system integrity, security guarantees, and architectural boundaries.

---

## 2. Non-Negotiable Rules
AI agents must:
- Read the entire repository before making changes.
- Treat existing code as the source of truth.
- Avoid assumptions about future features or intentions.

AI agents must not:
- Introduce new features unless explicitly instructed.
- Relax security constraints.
- Modify access control behavior without authorization.

---

## 3. Scope of Allowed Changes
Allowed:
- Documentation updates
- Bug fixes with clear reproduction
- Refactoring without behavioral change
- Adding tests for existing behavior

Disallowed:
- Schema changes without migrations
- Role or permission changes
- Security-related shortcuts

---

## 4. Code Interaction Rules
- Do not place business logic in routes.
- Use existing services and patterns.
- Follow module boundaries strictly.
- Preserve naming conventions and file structure.

---

## 5. Security Constraints
- CSRF protection must remain enabled.
- Authentication and authorization layers must not be bypassed.
- Sensitive data must never be logged or exposed.

---

## 6. Output Requirements
- Changes must be minimal and explicit.
- Every modification must be traceable.
- Documentation updates must reflect actual code behavior only.

---

## 7. Review and Validation
- AI-generated changes should be reviewed by a human.
- Any ambiguity must be resolved conservatively.
- When in doubt, do nothing and request clarification.

---

## 8. Failure Handling
- Do not attempt silent fixes.
- Surface errors clearly.
- Avoid partial or speculative implementations.
