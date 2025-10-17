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
