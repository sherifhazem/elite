# ELITE Backend – Initial Setup
Last Updated: 2025-10-18

The ELITE backend provides the foundational services for managing elite offers and related business logic. This initial setup prepares the project with a clean structure, environment configuration, and basic health monitoring endpoint.

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
    models/              # SQLAlchemy models
        __init__.py
        user.py
        company.py
        offer.py
    routes/              # Application blueprints and route definitions
        __init__.py
    services/            # Business logic and service layer implementations
        __init__.py
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
```

- `SECRET_KEY`: Used for securing sessions and cryptographic components.
- `SQLALCHEMY_DATABASE_URI`: PostgreSQL connection string used by SQLAlchemy.
- `REDIS_URL`: Redis instance used by both Redis client and Celery.
- `TIMEZONE`: Default timezone for Celery and application-level scheduling.

## Database Setup

This stage connects the application to PostgreSQL through SQLAlchemy and Flask-Migrate.

### Core Tables

- - **User (`users`)**: `id`, `username`, `email`, `password_hash`, `membership_level`, `joined_at`.
- **Company (`companies`)**: `id`, `name`, `description`, `created_at`.
- **Offer (`offers`)**: `id`, `title`, `base_discount`, `valid_until`, `company_id`, `created_at`.

### Migration Workflow

1. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
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

## Local Development

1. **Create and activate a virtual environment**

    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
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
