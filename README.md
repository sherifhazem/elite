# ELITE Backend – Initial Setup
Last Updated: 2025-10-17

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

- **User (`users`)**: `id`, `username`, `email`, `password_hash`, `joined_at`.
- **Company (`companies`)**: `id`, `name`, `description`, `created_at`.
- **Offer (`offers`)**: `id`, `title`, `discount_percent`, `valid_until`, `company_id`, `created_at`.

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

## API Endpoints

The CRUD API is namespaced under the `/api` prefix. All endpoints exchange JSON payloads and return the status codes listed in each section.

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
        "discount_percent": 20,
        "company_id": 3,
        "valid_until": "2025-02-01T23:59:59"
    }'
```

Successful response (`201 Created`):

```json
{
    "id": 5,
    "title": "New Year Discount",
    "discount_percent": 20.0,
    "valid_until": "2025-02-01T23:59:59",
    "company_id": 3,
    "created_at": "2025-01-17T10:15:00"
}
```

Possible errors:

- `400 Bad Request` when required fields are missing, the discount is not numeric, or `valid_until` is not ISO formatted.
- `404 Not Found` when the associated company or the target offer cannot be located.

> ℹ️ Use `curl` or Postman to exercise each endpoint after starting the Flask server. Ensure the content type is `application/json` for all mutation requests.

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
