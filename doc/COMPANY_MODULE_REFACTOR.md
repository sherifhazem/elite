# Company Module Refactor

## Summary
- Introduced a dedicated `company` blueprint at `app/modules/companies/routes.py` to own the public company registration flow.
- Relocated the company registration view, template, and JavaScript into the companies module so assets and routing share the same namespace.
- Updated navigation links to target `/company/register`, keeping member authentication pages focused on member accounts.

## Routing
- New browser route: `company.register_company` → `/company/register` (GET/POST).
- Blueprint registration occurs after the member auth blueprint inside `app/__init__.py` to preserve auth configuration while isolating company pages.
- API route for company registration remains under `app/modules/companies/routes/api_routes.py` (`/api/companies/register`).

## Templates and Static Assets
- Company registration template now lives at `app/modules/companies/templates/companies/register_company.html`.
- Supporting JavaScript relocated to `app/modules/companies/static/companies/js/company_registration_form.js` and loads via `url_for('company.static', ...)`.
- Shared auth base templates still render correctly through the existing `ChoiceLoader` stack, so layout and styling remain unchanged.

## Why separate from members
- The company onboarding path was previously embedded in `members/auth`, mixing member signup concerns with company intake.
- Moving the route and assets under `companies` clarifies ownership, aligns URL prefixes (`/company/*`), and reduces coupling between member auth and partner onboarding flows.

## CSRF and authentication impact
- The registration form continues to include `{{ form.hidden_tag() }}` to carry CSRF tokens after relocation.
- The login manager remains configured in `app/__init__.py`; relocating the route does not alter authentication enforcement or session handling.
- Middleware-based request cleaning still applies because the new blueprint reuses the same service layer (`register_company_account`).

## Before / After architecture
```
Before
- auth (members/auth/routes.py)
  - /register/company
  - templates/members/auth/register_company.html
  - static/members/js/company_registration_form.js

After
- company (companies/routes.py)
  - /company/register
  - templates/companies/register_company.html
  - static/companies/js/company_registration_form.js
  - company_portal* continues to serve authenticated company pages
```
`company_portal*` refers to the existing portal blueprint under `app/modules/companies/routes/__init__.py`.

## Operational notes
- Navigation buttons for company signup now call `url_for('company.register_company')` to match the new blueprint namespace.
- Logging and middleware remain unchanged; no additional logging hooks were required for the relocated route.

## Route cleanup and compatibility
- Removed the legacy `/register/company` handler under the `auth` blueprint to keep company onboarding fully within the `company` namespace.
- `/company/register` (`url_for("company.register_company")`) is the single source of truth for browser-based company signups and receives traffic from legacy bookmarks via a lightweight redirect.
- Templates updated in this sweep: `members/auth/choose_membership.html`, `members/auth/register_choice.html`, and `members/auth/register_select.html` now link exclusively to `company.register_company`.
- Frontend teams should load the registration script from `url_for('company.static', filename='js/company_registration_form.js')` (path: `app/modules/companies/static/companies/js/company_registration_form.js`); the old `members` static path has been removed.
