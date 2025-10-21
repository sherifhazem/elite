# ELITE Backend – Initial Setup
Last Updated: 2025-10-18

The ELITE backend provides the foundational services for managing elite offers and related business logic. This initial setup prepares the project with a clean structure, environment configuration, and basic health monitoring endpoint.

## Admin Dashboard Localization Update

- All admin dashboard templates now present their interface text in English, covering navigation labels, the settings management screens, and the communication center views.
- The existing layout, icons, and right-to-left orientation remain unchanged while the logout and settings entries use consistent English wording.

## Fix: Admin Settings Template Path
- Replaced "admin/layout.html" with "dashboard/base.html" in all admin settings templates.
- Resolved Jinja2 TemplateNotFound error.
- Verified Settings page loads correctly after fix.

## Feature: Company Application Review Workflow
- Added new admin actions for reviewing pending company applications.
- Admin can approve or request correction with custom notes.
- Integrated email notifications (approval / correction).
- Added status filtering (pending / approved / correction).
- Added secure correction link for company to update data.

## Prerequisites

- Python 3.11
- Flask >= 2.3
- Redis (for Celery and caching requirements)
- PostgreSQL 13+

## Project Structure

```text
app/
    __init__.py          # Initializes the Flask app, extensions, and blueprints
    config.py            # Loads environment variables and centralizes configuration
    company/             # Company portal blueprint and supporting modules
        __init__.py
        routes.py
        api.py
    models/              # SQLAlchemy models
        __init__.py
        user.py
        company.py
        offer.py
    routes/              # Application blueprints and route definitions
        __init__.py
    services/            # Business logic and service layer implementations
        __init__.py
    static/
        css/
            company.css
        js/
            company/
                offers.js
                redemptions.js
                settings.js
    templates/
        company/
            base.html
            dashboard.html
            offers.html
            offer_form.html
            redemptions.html
            settings.html
    utils/               # Shared utilities and helper functions
        __init__.py
migrations/              # Alembic migrations managed via Flask-Migrate
    env.py
    script.py.mako
    versions/
        20250117_01_initial_tables.py
run.py                   # Entry point for running the Flask development server
README.md                # Project documentation
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```dotenv
SECRET_KEY=super-secret-key
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/elite
REDIS_URL=redis://localhost:6379/0
TIMEZONE=Asia/Riyadh
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER="Elite Discounts <your_email@gmail.com>"
```

- `SECRET_KEY`: Used for securing sessions and cryptographic components.
- `SQLALCHEMY_DATABASE_URI`: PostgreSQL connection string used by SQLAlchemy.
- `REDIS_URL`: Redis instance used by both Redis client and Celery.
- `TIMEZONE`: Default timezone for Celery and application-level scheduling.
- `MAIL_*`: SMTP configuration for sending verification and password reset emails.

## Email System

The authentication service now delivers verification and password reset emails using SMTP credentials defined in `.env`.

### Required Environment Variables

- `MAIL_SERVER` – SMTP host (default: `smtp.gmail.com`).
- `MAIL_PORT` – SMTP port (default: `587`).
- `MAIL_USERNAME` – Account used to authenticate with the SMTP server.
- `MAIL_PASSWORD` – App-specific password or SMTP credential.
- `MAIL_DEFAULT_SENDER` – Display name and email for outgoing messages.

### Endpoints

- `POST /api/auth/register` – Sends a verification email after creating a new account.
- `GET /api/auth/verify/<token>` – Confirms the user's email address and activates the account.
- `POST /api/auth/reset-request` – Issues a reset token and emails the reset link.
- `POST /api/auth/reset-password/<token>` – Accepts a new password using the emailed token.

### Flow Overview

1. Registration triggers a verification email containing a signed tokenized link.
2. Visiting the verification link activates the account by toggling `is_active` to `True`.
3. Forgotten password requests send a one-time reset link to the registered email.
4. Submitting a new password with the reset token updates the stored hash and invalidates the link by expiration (default 1 hour).

## Database Setup

This stage connects the application to PostgreSQL through SQLAlchemy and Flask-Migrate.

### Core Tables

- **User (`users`)**: `id`, `username`, `email`, `password_hash`, `membership_level`, `joined_at`.
- **Company (`companies`)**: `id`, `name`, `description`, `created_at`, `owner_user_id`, `logo_url`, `notification_preferences` (JSON).
- **Offer (`offers`)**: `id`, `title`, `description`, `base_discount`, `valid_until`, `company_id`, `created_at`.

### Migration Workflow

1. Ensure dependencies are installed (see the dependency list below):
   ```bash
   pip install \
       alembic==1.17.0 \
       amqp==5.3.1 \
       billiard==4.2.2 \
       blinker==1.9.0 \
       celery==5.5.3 \
       click==8.3.0 \
       click-didyoumean==0.3.1 \
       click-plugins==1.1.1.2 \
       click-repl==0.3.0 \
       colorama==0.4.6 \
       flask==3.1.2 \
       flask-cors==6.0.1 \
       Flask-Migrate==4.1.0 \
       flask-sqlalchemy==3.1.1 \
       greenlet==3.2.4 \
       itsdangerous==2.2.0 \
       jinja2==3.1.6 \
       kombu==5.5.4 \
       mako==1.3.10 \
       markupsafe==3.0.3 \
       packaging==25.0 \
       pillow==12.0.0 \
       prompt-toolkit==3.0.52 \
       psycopg2-binary==2.9.11 \
       pybald-routes==2.11 \
       PyJWT==2.10.1 \
       python-dateutil==2.9.0.post0 \
       python-dotenv==1.1.1 \
       qrcode==8.2 \
       redis==6.4.0 \
       repoze.lru==0.7 \
       six==1.17.0 \
       sqlalchemy==2.0.44 \
       typing-extensions==4.15.0 \
       tzdata==2025.2 \
       vine==5.1.0 \
       wcwidth==0.2.14 \
       werkzeug==3.1.3
   ```

## Endpoint Naming Standardization
- Unified endpoint names for admin routes:
  - admin.settings_home
  - admin.site_settings_roles
  - admin.admin_logout
- Updated all templates and route calls accordingly.
- Verified url_for() references after changes.
2. Set the Flask application context:
   ```bash
   export FLASK_APP=run.py
   ```
3. Initialize the migration repository (only once):
   ```bash
   flask db init
   ```
4. Generate the initial migration:
   ```bash
   flask db migrate -m "Initial tables"
   ```
5. Apply the migration to the PostgreSQL database:
   ```bash
   flask db upgrade
   ```

### Database Environment Variables

- `SQLALCHEMY_DATABASE_URI` must point to a reachable PostgreSQL instance.
- For local development, the default URI assumes the `elite` database exists with accessible credentials.

> **Note:** This phase represents the "التهيئة الأساسية للبيانات" (basic data initialization). The subsequent phase will introduce the CRUD API layer on top of these models.

## Roles & Permissions System

The ELITE platform now enforces a role-based access control layer across the API, admin dashboard, company portal, and member portal.

| Role        | Access Scope                                                   |
|-------------|----------------------------------------------------------------|
| member      | `/portal/*` – offers, membership profile, notifications        |
| company     | `/company/*` – manage only the company's own offers            |
| admin       | `/admin/*` – global supervision and reporting                  |
| superadmin  | Full control over all areas and advanced administration tools |

- User accounts include the new `role`, `is_active`, and optional `company_id` fields.
- Administrators manage roles via the **Admin → Roles** page, which provides activation toggles and role selectors with inline feedback.
- Granular permissions are prepared through the `permissions` and `user_permissions` tables for future expansions.

### Decorator Usage

Protect server routes with the `require_role` decorator:

```python
from app.services.roles import require_role

@blueprint.route("/admin/secure-endpoint")
@require_role("admin")
def secure_action():
    ...
```

The decorator allows the target role and higher-privileged roles defined in the access matrix (e.g., `superadmin` can access all admin routes). Unauthorized requests respond with `401` or `403` as appropriate.

### Migration Notes

Apply the `b7d91a5f3c1a_add_role_and_is_active_fields_to_users.py` Alembic revision after configuring a reachable PostgreSQL instance:

```bash
flask db upgrade
```

> **Important:** The migration script removes the legacy `is_admin` flag, introduces the role columns, and prepares the permissions tables. Ensure the database service is running before executing the upgrade.

## Local Development

1. **Create and activate a virtual environment**

    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    ```

2. **Install dependencies**

    ```bash
    pip install \
        alembic==1.17.0 \
        amqp==5.3.1 \
        billiard==4.2.2 \
        blinker==1.9.0 \
        celery==5.5.3 \
        click==8.3.0 \
        click-didyoumean==0.3.1 \
        click-plugins==1.1.1.2 \
        click-repl==0.3.0 \
        colorama==0.4.6 \
        flask==3.1.2 \
        flask-cors==6.0.1 \
        Flask-Migrate==4.1.0 \
        flask-sqlalchemy==3.1.1 \
        greenlet==3.2.4 \
        itsdangerous==2.2.0 \
        jinja2==3.1.6 \
        kombu==5.5.4 \
        mako==1.3.10 \
        markupsafe==3.0.3 \
        packaging==25.0 \
        pillow==12.0.0 \
        prompt-toolkit==3.0.52 \
        psycopg2-binary==2.9.11 \
        pybald-routes==2.11 \
        PyJWT==2.10.1 \
        python-dateutil==2.9.0.post0 \
        python-dotenv==1.1.1 \
        qrcode==8.2 \
        redis==6.4.0 \
        repoze.lru==0.7 \
        six==1.17.0 \
        sqlalchemy==2.0.44 \
        typing-extensions==4.15.0 \
        tzdata==2025.2 \
        vine==5.1.0 \
        wcwidth==0.2.14 \
        werkzeug==3.1.3
    ```

3. **Run the application**

    ```bash
    export FLASK_APP=app
    flask run
    ```

    Alternatively, run through the provided entry point:

    ```bash
    python run.py
```

## Testing

After starting the server, visit [`http://localhost:5000/health`](http://localhost:5000/health) to confirm the backend is responsive. The endpoint returns the JSON payload:

```json
{"status": "ok"}
```

## Known Fixes

- تم تصحيح العلاقة بين User و Company بإضافة `foreign_keys=[company_id]` لمنع الغموض في ORM.

## Fix: Logout Button & Flask-Login Integration
- Added LoginManager initialization to enable logout_user().
- Configured user_loader for User model.
- Updated admin_logout route to clear elite_token cookie.
- Ensured consistent user authentication context for Flask-Login and JWT.

## Membership Upgrade System

The member portal now allows authenticated users to elevate their membership tier directly from the profile page.

- **Endpoint:** `POST /portal/upgrade`
- **Request Body:**

  ```json
  {"new_level": "Silver"}
  ```

## Login & Redirect System

المستخدمون يمكنهم الآن تسجيل الدخول عبر واجهة ويب مخصصة يتم تحميلها من المسار `/login-page`.

1. يفتح المستخدم الرابط `/login-page` ويُدخل البريد الإلكتروني وكلمة المرور.
2. يرسل المتصفح طلب `POST` إلى `/api/auth/login` ويتلقى JSON يحتوي على الـ JWT والدور.
3. يتم تخزين التوكن في `localStorage` وCookie آمنة ثم يتم توجيه المستخدم تلقائيًا إلى الواجهة المناسبة بناءً على دوره.

- **توجيه الأدوار:**
  - `member` → `/portal/`
  - `company` → `/company/`
  - `admin` أو `superadmin` → `/admin/`

- **مثال استجابة ناجحة:**

  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "role": "member",
    "is_active": true,
    "redirect_url": "/portal/"
  }
  ```

- **مثال استجابة فاشلة:**

  ```json
  {"error": "Invalid credentials."}
  ```

  Acceptable values: `"Silver"`, `"Gold"`, or `"Premium"` (upgrades are only allowed to higher tiers).
- **Successful Response:**

  ```json
  {"message": "Membership upgraded to Gold"}
  ```

### How to Test

1. Sign in through the portal so that a valid JWT token is stored (header or cookie).
2. Open `/portal/profile` and use the **Upgrade Membership** form to choose a higher level.
3. Alternatively, send a `POST` request with the JSON body shown above using Postman or curl. Include the JWT as a `Bearer` token or cookie.
4. Confirm the success alert appears and that the badge on the profile reflects the new membership tier.

### Security Notes

- The upgrade API always validates the JWT token; direct requests without authentication receive `401 Unauthorized`.
- Only the predefined membership levels (`Basic`, `Silver`, `Gold`, `Premium`) are accepted by the backend to prevent arbitrary values.

## Company Portal

The `/company/*` blueprint delivers a desktop-first management console for business owners. Access is restricted to accounts with the `company` role (or `superadmin` when a company association exists).

### Routes

- `/company/` → redirects to the dashboard overview.
- `/company/dashboard` → stats cards and a table of the latest 10 redemptions.
- `/company/offers` → CRUD management of the company's own offers via fetch-powered forms.
- `/company/redemptions` → verify redemption codes manually or by QR scanning.
- `/company/settings` → update the public profile, logo URL, and notification preferences.

### Key Workflows

1. **Create or edit an offer**
   - Launch the modal from `/company/offers`.
   - Submit the form via AJAX to `/company/offers` or `/company/offers/<id>`.
   - Optionally enable *Send notifications* to trigger `services.notifications.broadcast_new_offer`.
2. **Redeem a member code**
   - Staff enters the code (or scans it) on `/company/redemptions`.
   - `/company/redemptions/verify` ensures the code belongs to the current company and has not expired.
   - `/company/redemptions/confirm` finalizes the redemption with audit logging via `current_app.logger`.
3. **Maintain company profile**
   - `/company/settings` persists `name`, `description`, `logo_url`, and boolean notification flags.

### Security Notes

- All portal routes use `require_role("company")` and filter every lookup by `company_id`.
- Attempts to load, update, or delete another company's data return `403 Forbidden`.
- Redemption APIs reject expired codes, duplicates, or mismatched company IDs.

### Screenshots

Capture dashboard, offers, redemptions, and settings views from a running instance to populate documentation. Image assets are intentionally omitted from this repository per delivery constraints.

### Migration Reminder

The new fields (`Company.owner_user_id`, `Company.logo_url`, `Company.notification_preferences`, and `Offer.description`) require an Alembic migration. Generate it with:

```bash
flask db migrate -m "Add company portal fields"
flask db upgrade
```


## Offer Redemption System

The redemption workflow allows members to generate single-use codes (and QR images) that participating companies can validate instantly through their dedicated portal page.

### Lifecycle

1. **Member activation** – The member calls `POST /api/redemptions/` with the target `offer_id`. A 12-character code and high-resolution QR image are generated and stored under `app/static/qrcodes/`.
2. **Company confirmation** – Company staff visits `/company/redemptions`, enters the code or scans the QR token, and the system issues `PUT /api/redemptions/<code>/confirm`.
3. **Audit trail** – Each confirmation updates the `offer_redemptions` table, stamps `redeemed_at`, and queues notifications for the member and administrators.

### API Examples

```http
POST /api/redemptions/
Content-Type: application/json

{"offer_id": 42}
```

```http
GET /api/redemptions/AB12CD34EF56
Authorization: Bearer <token>
```

```http
PUT /api/redemptions/AB12CD34EF56/confirm
Content-Type: application/json

{"qr_token": "5d2d4d78-2a5f-4e3c-9ab5-0f2e8c67c123"}
```

### Security Notes

- Codes expire automatically 48 hours after creation; expired codes return `410 Gone` from the QR endpoint.
- Each offer can only be activated once per member while the previous code remains valid.
- Confirmation is limited to the company that owns the offer, preventing cross-company redemption.
- QR tokens include a UUID payload encoded in the image, providing an additional factor for scanning-based confirmations.

## Mobile-First User Portal Design

The `/portal` experience has been rebuilt with a mobile-first mindset to mirror native iOS and Android applications while keeping the `/admin` and `/company` dashboards in their desktop-oriented layout.

- **App Shell:** Each portal route now renders inside a compact mobile viewport with a sticky header, animated view transitions, and a persistent bottom navigation bar for Home, Offers, Profile, and Notifications.
- **Mobile Interactions:** Smooth in-app navigation, pull-to-refresh, modal offer previews, toast confirmations, and loading spinners are implemented through the lightweight `app/static/js/main.js` controller.
- **Visual Identity:** The refreshed stylesheet (`app/static/css/style.css`) applies the official palette, rounded components, and Poppins/Inter typography. Core colors include deep navy `#0b1f3a` as the primary, warm gold `#f2c14e` for accents, and soft gray tints (`#f5f7fb`, `#e4e8f0`) for layered surfaces.

- **Membership Card:** The profile screen showcases a full-width membership card rendered with layered CSS gradients, and the **Download My Card** action still exports a branded image on demand.
- **Screenshots:** Capture fresh mobile frames using your preferred simulator or device before release; create `app/static/images/screenshots/` locally and drop them there only when marketing hand-offs require the assets.

> **Note:** The mobile-first design applies exclusively to `/portal/*` routes. Administrative and company-facing dashboards remain optimized for desktop workflows without any layout changes.

## Admin Interface Design

تم تحسين واجهة لوحة الإدارة باستخدام Bootstrap Layout وألوان Elite الرسمية.

## Admin Dashboard CRUD Features

The Elite Admin Panel now delivers full create, read, update, and delete (CRUD) workflows for the platform's core entities. All operations are backed by SQLAlchemy transactions and surfaced through responsive Bootstrap-powered templates located under `app/admin/templates/dashboard/`.

### User Operations

- Browse all registered accounts, their membership levels, and administrative privileges.
- Add new members with secure password hashing directly from the dashboard.
- Update usernames, email addresses, membership levels, and optionally reset passwords.
- Remove inactive or duplicate users after confirmation prompts.

### Company Operations

- Review the partner catalogue, including creation timestamps and descriptions.
- Register new companies with descriptive summaries.
- Edit existing partner information to keep marketplace data accurate.
- Delete companies that are no longer part of the program.

### Offer Operations

- Inspect current promotions alongside their associated companies and expiry dates.
- Publish new offers with configurable discounts and optional expiry windows.
- Update discounts, titles, validity ranges, or linked companies at any time.
- Retire outdated offers instantly.

## Admin Discount Management

Administrators can fine-tune membership incentives directly from the `/admin/offers` dashboard page.

### Dashboard Overview

- Each offer row now displays the base discount alongside dynamically calculated values for Silver, Gold, and Premium tiers.
- Color-coded badges help distinguish membership levels at a glance: Basic (gray), Silver (silver), Gold (gold), and Premium (purple).
- Action buttons provide quick access to discount editing, full offer management, or archival via deletion.

### Updating Base Discounts

1. Sign in as an administrator and open **Offers** from the navigation bar (URL: `/admin/offers`).
2. Choose **Edit Discount** for the desired offer to open a focused form.
3. Enter the new `base_discount` value in percentage form and submit.
4. A success flash message confirms the update and returns you to the offers table.

> **Tip:** The edit view summarises the resulting Basic, Silver, Gold, and Premium discounts so you can validate the membership impact before saving.

### Behind the Scenes

- The system stores a single `base_discount` per offer and applies predefined uplifts for Silver (+5%), Gold (+10%), and Premium (+15%) members.
- Any change committed through the dashboard is reflected immediately in the public API responses (e.g., retrieving the offer as a Premium member now returns the recalculated discount).
- Suggested validation workflow: adjust a discount in the admin UI, then fetch the same offer through the Premium API endpoint to ensure parity.

### Usage Flow

1. Authenticate with a JWT token tied to an account where `is_admin=True`.
2. Navigate to `/admin/` to access the dashboard overview cards.
3. Use the navigation bar to open the Users, Companies, or Offers tables.
4. Launch dedicated Add or Edit forms via the action buttons, submit the changes, and monitor success messages delivered through Flask flash alerts.

#### Interface Preview

| Section | Primary Actions | Quick Links |
| --- | --- | --- |
| Users | Add, Edit, Delete accounts with membership control | `/admin/users`, `/admin/users/add` |
| Companies | Maintain partner directory | `/admin/companies`, `/admin/companies/add` |
| Offers | Manage promotional campaigns | `/admin/offers`, `/admin/offers/add` |

### Security Notes

- Dashboard access is restricted to authenticated administrators. Always validate the `is_admin` flag before issuing session tokens.
- Perform CRUD actions over HTTPS and rotate the `SECRET_KEY` regularly to protect session integrity.
- Audit admin usage and rotate credentials periodically to maintain compliance.

## API Endpoints

The CRUD API is namespaced under the `/api` prefix. All endpoints exchange JSON payloads and return the status codes listed in each section.
## Authentication API

The authentication layer exposes JWT-based routes under `/api/auth`. All payloads must be JSON and all responses are JSON-encoded.

- - `POST /api/auth/register` – Create a new user account. Returns `201 Created` with the new user's identifier, membership level (`Basic` by default), and confirmation message when successful. Duplicate usernames or emails return `400 Bad Request`.
- `POST /api/auth/login` – Authenticate using email and password. Returns `200 OK` with a bearer token when the credentials are correct, or `401 Unauthorized` when they are not.
- - `GET /api/auth/profile` – Retrieve the authenticated user's profile, including the current membership level. Requires a valid JWT sent in the `Authorization` header. Returns `200 OK` with user details or `401 Unauthorized` if the token is missing or invalid.
- `PUT /api/auth/membership` – Update the authenticated user's membership level. Expects a JSON body with the desired tier and returns `200 OK` with the updated state when the level is valid.

Send the JWT in subsequent requests using the standard bearer header:

```http
Authorization: Bearer <token>
```

### Security Notes

- Passwords are never stored in plain text; they are hashed using `werkzeug.security` helpers before persistence.
- Always use HTTPS in production to prevent token interception and replay attacks.
- 
### Membership Levels

The ELITE platform now distinguishes between four membership tiers that control the promotions a user can see:

- **Basic** – الوصول محدود للعروض (limited access to general offers).
- **Silver** – عروض عامة متوسطة (standard platform-wide promotions).
- **Gold** – عروض موسعة تشمل شراكات مميزة (extended offers with premium partners).
- **Premium** – خصومات حصرية ومزايا خاصة (exclusive discounts and loyalty perks).

Every new account starts at the **Basic** tier. Membership levels are stored in the `users.membership_level` column and surfaced in authentication responses, allowing the frontend to tailor the experience immediately after login.

#### Updating a Membership Level via API

Use the authenticated endpoint to change the tier:

```http
PUT /api/auth/membership
Authorization: Bearer <token>
Content-Type: application/json

{
    "membership_level": "Gold"
}
```

Successful response:

```json
{
    "id": 42,
    "membership_level": "Gold",
    "message": "Membership level updated successfully."
}
```

Administrators can also update an individual member directly through the users service when elevated privileges are in place:

```http
PATCH /api/users/<user_id>/membership
Content-Type: application/json

{
    "membership_level": "Premium"
}
```

The response body mirrors the standard user payload, enabling dashboards to refresh the membership tier without an additional fetch.

> **Admin roadmap:** requests may include a `user_id` field to target a specific account. Until role-based access control is introduced, attempting to change another user's tier returns `403 Forbidden`.

#### Profile Response Example

The `/api/auth/profile` payload now embeds the membership value alongside the other user attributes:

```json
{
    "id": 42,
    "username": "elite_user",
    "email": "elite@example.com",
    "membership_level": "Silver",
    "joined_at": "2025-01-17T12:00:00"
}
```
### Users

- `GET /api/users/` – Retrieve all registered users.
- `POST /api/users/` – Create a new user.
- `PUT /api/users/<id>` – Update an existing user.
- `DELETE /api/users/<id>` – Remove a user.

Example create request:

```bash
curl -X POST http://localhost:5000/api/users/ \
    -H "Content-Type: application/json" \
    -d '{
        "username": "elite_user",
        "email": "elite@example.com",
        "password_hash": "plain-or-hashed"
    }'
```

Successful response (`201 Created`):

```json
{
    "id": 1,
    "username": "elite_user",
    "email": "elite@example.com",
    "joined_at": "2025-01-17T12:00:00"
}
```

Possible errors:

- `400 Bad Request` when required fields are missing or the username/email already exist.
- 
## User Portal Interface

The member-facing portal delivers a simple dashboard where authenticated users can review their personalized discounts, browse curated offers, and confirm their account details. The feature set is implemented purely with Flask, Bootstrap, and Jinja templates.

### Template & Asset Layout

```text
app/templates/portal/
    base.html        # Layout wrapper with shared navigation, footer, and asset links
    home.html        # Landing view with welcome banner and membership badges
    offers.html      # Personalized offers table using dynamic discount logic
    profile.html     # Bootstrap card summarizing the member profile

app/static/
    css/style.css    # Extended styling aligned with the ELITE palette
    js/main.js       # Lightweight enhancements for the portal experience
    images/logo.png  # Branding asset displayed in the navigation bar
```

All portal pages inherit from `portal/base.html`, ensuring the navigation links (Home, Offers, Profile) remain consistent while the active section is highlighted for clarity.

### Dynamic Discount Rendering

Each offer row in `offers.html` uses `Offer.get_discount_for_level()` to compute the correct percentage for the visitor's membership tier. The active JWT token is resolved from either the `Authorization: Bearer` header or an `elite_token` cookie before querying offers. When a valid user is identified, the membership level is injected into every rendered template so the correct discount badge and styling are displayed.

### Testing the Portal

1. Launch the Flask development server and authenticate to obtain a JWT token.
2. Visit [`/portal/`](http://localhost:5000/portal/) to confirm the welcome banner shows your username and tier badge.
3. Navigate to [`/portal/offers`](http://localhost:5000/portal/offers) and verify the discount column reflects your membership uplift across all listed offers.
4. Open [`/portal/profile`](http://localhost:5000/portal/profile) to ensure the Bootstrap card displays username, email, and membership level. The upgrade button remains disabled until checkout flows are implemented.

### Color Palette Reference

The interface follows the tones captured in `Color Palette for Design Project.png`:

| Purpose | Hex | Description |
| --- | --- | --- |
| Midnight Navy (background accents) | `#0F172A` | Deep foundation tone for headings and navigation text |
| Slate Gray (supporting text) | `#7B8794` | Neutral copy color for descriptions |
| Soft Silver (Basic tier) | `#C0C5D1` | Badge background for introductory members |
| Metallic Silver (Silver tier) | `#C0C0C0` | Badge background for the Silver tier |
| Elite Gold (Gold tier) | `#D4AF37` | Highlighted badge for Gold members |
| Royal Purple (Premium tier) | `#6F42C1` | Primary accent gradient and Premium badge |
| Soft Violet (gradient highlight) | `#B68CF2` | Secondary gradient color for call-to-action buttons |
| Warm White (page background) | `#F6F7FB` | Subtle off-white background for content sections |

Use these references when extending the portal to maintain visual consistency with the ELITE identity.
- `404 Not Found` when updating or deleting a non-existent user.

### Companies

- `GET /api/companies/` – Retrieve all companies.
- `POST /api/companies/` – Create a new company profile.
- `PUT /api/companies/<id>` – Update company details.
- `DELETE /api/companies/<id>` – Remove a company.

Example update request:

```bash
curl -X PUT http://localhost:5000/api/companies/3 \
    -H "Content-Type: application/json" \
    -d '{
        "description": "Updated partnership summary."
    }'
```

Successful response (`200 OK`):

```json
{
    "id": 3,
    "name": "Tech Corp",
    "description": "Updated partnership summary.",
    "created_at": "2025-01-17T09:00:00"
}
```

Possible errors:

- `400 Bad Request` when the company name already exists.

## 🔧 تحديثات الإصدار - إصلاح الاستيرادات الدائرية

- **app/__init__.py**
  - نوع التعديل: تحسين ترتيب الاستيراد وتحديث المسارات النسبية.
  - سبب التعديل: منع الاستيراد الدائري وضمان تهيئة المكونات قبل تسجيل الـ Blueprints.
- **app/models/__init__.py**
  - نوع التعديل: إصلاح استيراد لاستخدام المسارات النسبية مع الكائن `db`.
  - سبب التعديل: منع الاستيراد الدائري وتحسين اتساق الحزمة.
- **app/models/user.py**
  - نوع التعديل: إصلاح استيراد الكائن `db` بمسار نسبي.
  - سبب التعديل: منع الاستيراد الدائري بين الحزم.
- **app/models/company.py**
  - نوع التعديل: إصلاح استيراد الكائن `db` بمسار نسبي.
  - سبب التعديل: منع الاستيراد الدائري بين الحزم.
- **app/models/offer.py**
  - نوع التعديل: إصلاح استيراد الكائن `db` بمسار نسبي.
  - سبب التعديل: منع الاستيراد الدائري بين الحزم.
- **app/routes/user_routes.py**
  - نوع التعديل: إصلاح استيرادات `db` و`User` بمسارات نسبية وإزالة التكرار.
  - سبب التعديل: منع الاستيراد الدائري وتحسين بنية المسارات.
- **app/routes/company_routes.py**
  - نوع التعديل: إصلاح استيرادات `db` و`Company` بمسارات نسبية وإزالة التكرار.
  - سبب التعديل: منع الاستيراد الدائري وتحسين بنية المسارات.
- **app/routes/offer_routes.py**
  - نوع التعديل: إصلاح استيرادات `db` و`Company` و`Offer` بمسارات نسبية.
  - سبب التعديل: منع الاستيراد الدائري وتحسين بنية المسارات.
- `404 Not Found` when the specified company does not exist.

### Offers

- `GET /api/offers/` – Retrieve all offers.
- `POST /api/offers/` – Create a new offer.
- `PUT /api/offers/<id>` – Update an existing offer.
- `DELETE /api/offers/<id>` – Remove an offer.

Example create request:

```bash
curl -X POST http://localhost:5000/api/offers/ \
    -H "Content-Type: application/json" \
    -d '{
        "title": "New Year Discount",
        "base_discount": 10,
        "company_id": 3,
        "valid_until": "2025-02-01T23:59:59"
    }'
```

Successful response (`201 Created`):

```json
{
    "id": 5,
    "title": "New Year Discount",
    "base_discount": 10.0,
    "discount_percent": 10.0,
    "valid_until": "2025-02-01T23:59:59",
    "company_id": 3,
    "created_at": "2025-01-17T10:15:00"
}
```

Possible errors:

- `400 Bad Request` when required fields are missing, the discount is not numeric, or `valid_until` is not ISO formatted.
- `404 Not Found` when the associated company or the target offer cannot be located.

> ℹ️ Use `curl` or Postman to exercise each endpoint after starting the Flask server. Ensure the content type is `application/json` for all mutation requests.

## Dynamic Discount Logic

Membership-aware pricing is now handled inside `app/models/offer.py` via the `Offer.get_discount_for_level()` helper. The method
calculates the final discount percent by applying a tier-specific adjustment to the stored `base_discount` value.

| Membership | Discount Adjustment |
|-------------|--------------------|
| Basic       | +0%                |
| Silver      | +5%                |
| Gold        | +10%               |
| Premium     | +15%               |

For example, assume an offer has a `base_discount` of `12.5`. When a Premium member queries `GET /api/offers/`, the response includes the dynamically adjusted discount percent:

```json
[
    {
        "id": 7,
        "title": "Weekend Flash Sale",
        "base_discount": 12.5,
        "discount_percent": 27.5,
        "valid_until": "2025-11-01T21:00:00",
        "company_id": 3,
        "created_at": "2025-10-18T14:20:00"
    }
]
```

The API automatically inspects the bearer token to determine the membership level. If the request is unauthenticated or the token is invalid, the system falls back to the **Basic** tier.

## Frontend Initialization

_Last updated: 2025-10-17_

The project now includes a minimal Flask frontend for the Elite Discounts platform. Use this section as a reference when iterating on the presentation layer.

### Template and Static Structure

```text
app/
    templates/
        base.html        # Shared layout for all pages
        index.html       # Landing page content
    static/
        css/
            style.css    # Global styles used by the base layout
        js/              # Placeholder for future scripts
        images/          # Placeholder for shared media assets
```

### Customizing Styles and Templates

- Update `app/static/css/style.css` to adjust colors, typography, or layouts across the site.
- Extend `app/templates/base.html` to add navigation, footer content, or additional blocks as needed.
- Create new templates within `app/templates/` that `{% extends "base.html" %}` to reuse the shared structure.

### Available Routes

- `/` – Renders the homepage template.
- `/about` – Returns a short description of Elite Discounts.
- `/health` – Provides the JSON health check `{"status": "ok"}`.

## Notifications System

The platform now delivers in-app notifications to members whenever impactful events occur.

### Data Model

- **Notification (`notifications`)**: `id`, `user_id`, `type`, `title`, `message`, `link_url`, `is_read`, `created_at`, `metadata_json`.
- Notifications always belong to a single user and default to an unread state until explicitly marked as read.

### Celery Tasks

- `notifications.create`: persists an individual notification.
- `notifications.broadcast_offer`: creates notifications for every user in manageable batches so the worker avoids loading the entire member base at once.

Celery relies on the existing Redis broker/configuration. Start a worker with:

```bash
celery -A app.celery worker --loglevel=info
```

Run the Flask development server in a separate terminal:

```bash
flask run
```

### REST API

- `GET /api/notifications/?page=1&per_page=20` – returns a paginated list of the authenticated user's notifications plus the unread total.
  ```json
  {
    "notifications": [
      {
        "id": 101,
        "type": "new_offer",
        "title": "New offer: Spring Savings",
        "message": "Spring Savings now includes at least 12.50% off.",
        "link_url": "/portal/offers",
        "is_read": false,
        "created_at": "2025-01-20T10:45:00",
        "metadata": {"offer_id": 9, "base_discount": 12.5}
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 5,
    "unread_count": 3
  }
  ```
- `PUT /api/notifications/<id>/read` – marks a single notification as read.
- `PUT /api/notifications/read-all` – marks every notification for the current user as read.
- `DELETE /api/notifications/<id>` – removes a notification owned by the requester.

All endpoints require a valid JWT delivered via `Authorization: Bearer <token>` or the `elite_token` cookie.

### Integration Points

- Membership upgrades call `notify_membership_upgrade`, queuing a personalised message for the user.
- Offer creation and base-discount updates call `broadcast_new_offer`, queuing a background job to inform every member.
- The admin dashboard includes opt-in checkboxes and a "Notify Members" action to trigger broadcasts directly after saving changes.

### Portal Experience

- `/portal/notifications` lists the newest 200 notifications with read/unread styling and quick actions.
- The navigation bar displays a bell badge that updates automatically after marking notifications as read.
- Buttons on the page use the new `markNotificationRead(id)` and `markAllNotificationsRead()` JavaScript helpers that call the API via `fetch`.

### Security Notes

- All notification APIs verify ownership: attempts to read, mark, or delete another user's notifications return `404`.
- Authenticated requests are mandatory; anonymous users receive `401 Unauthorized` responses.

## Manual Test Plan

1. **Membership upgrade notification** – log in, upgrade a membership through `/portal/profile`, and confirm the queued notification appears.
2. **Offer broadcast** – create or update an offer (enable **Send notifications**) from `/admin/offers`, then verify members receive the "new offer" notification.
3. **Portal interaction** – visit `/portal/notifications`, mark a single notification as read, mark all as read, and confirm the navigation badge updates accordingly.

## Reports & Analytics Dashboard

The administrative analytics suite at `/admin/reports` surfaces near-real-time indicators for platform growth and marketplace performance.

### Visual Components

- **Stats Cards:** summarize total users, partner companies, and active offers with supporting context on recent growth.
- **Pie Chart:** membership distribution across Basic, Silver, Gold, and Premium tiers for instant segmentation insight.
- **Bar Chart:** seven-day registration timeline to reveal daily acquisition trends.
- **Line Chart:** weekly offer creation trend line illustrating catalogue momentum.
- **Recent Offers Table:** highlights the five most recent promotions with discount and validity metadata.

### Routes & Data Sources

#### Registration & Onboarding

- `GET /register/select` – presents the visitor with member or company registration choices.
- `GET/POST /register/member` – serves the member signup form and processes direct submissions.
- `GET/POST /register/company` – serves the company signup form and processes direct submissions.

#### Legacy Aliases

- `/portal/home` → `/portal/` (maps to `url_for('portal.home')`).
- `/admin/dashboard` → `/admin/` (maps to `url_for('admin.dashboard_home')`).

#### Admin Analytics

- `GET /admin/reports` – renders the interactive dashboard layout.
- `GET /admin/api/summary` – provides the JSON snapshot consumed by the JavaScript charts.
- `GET /admin/reports/export` – streams a generated PDF summarizing the latest metrics.

The summary payload combines the following datasets:

- Total users, new registrations (7-day window), and membership-level counts.
- Partner company totals with 30-day onboarding figures.
- Offer analytics covering active/expired counts, average base discount, trend breakdown, and recent offers.
- Membership distribution prepared for chart rendering.
- Daily registration activity for the last seven days.

### Implementation Notes

- Data is aggregated in-memory using lightweight SQLAlchemy queries and refreshed on the client every 60 seconds.
- All administrative routes continue to enforce `is_admin=True` validation through the existing `admin_required` decorator.
- Chart rendering relies exclusively on Chart.js delivered via CDN, with custom styling in `app/static/css/reports.css`.
- PDF exports are produced through ReportLab with on-demand generation—no historical snapshots are persisted.

## Known Limitations / Redirects

- Historic links to `/portal/home` and `/admin/dashboard` now redirect to their canonical destinations to prevent `404` responses.
- Registration flows continue to depend on the JSON APIs for account creation; browser forms fall back to the same logic to avoid drift.
- This refresh did not change the database schema or SQLAlchemy models.

## Manual Quick Tests

Run these smoke checks after deploying or touching the registration flows:

1. Visit `/register/select` and confirm the member/company options point to the correct endpoints.
2. Complete `/register/member` and verify the welcome email + notification triggers run.
3. Complete `/register/company` and verify the owner account + welcome flows run.
4. Open `/portal/home` and confirm it redirects to the live portal home view without errors.
5. Open `/admin/dashboard` and confirm it redirects to the admin landing page without errors.
6. Traverse the main navigation templates and confirm `url_for` is used for dynamic links.

## Feature: Company Suspension & Reactivation
- Added suspend/reactivate actions in admin company management.
- Integrated email notifications for suspension and reactivation.
- Updated company model with status field.
- Prevented suspended companies from accessing their portal.
- All operations are non-destructive (no deletions).
