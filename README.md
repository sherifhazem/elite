# ELITE Backend – Initial Setup

The ELITE backend provides the foundational services for managing elite offers and related business logic. This initial setup prepares the project with a clean structure, environment configuration, and basic health monitoring endpoint.

## Prerequisites

- Python 3.11
- Flask >= 2.3
- Redis (for Celery and caching requirements)

## Project Structure

```text
app/
    __init__.py          # Initializes the Flask app, extensions, and blueprints
    config.py            # Loads environment variables and centralizes configuration
    models/              # Future SQLAlchemy models
        __init__.py
    routes/              # Application blueprints and route definitions
        __init__.py
    services/            # Business logic and service layer implementations
        __init__.py
    utils/               # Shared utilities and helper functions
        __init__.py
migrations/              # Placeholder for database migration scripts (e.g., Alembic)
run.py                   # Entry point for running the Flask development server
README.md                # Project documentation
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```dotenv
SECRET_KEY=super-secret-key
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/elite
REDIS_URL=redis://localhost:6379/0
TIMEZONE=Asia/Riyadh
```

- `SECRET_KEY`: Used for securing sessions and cryptographic components.
- `DATABASE_URL`: SQLAlchemy database connection string.
- `REDIS_URL`: Redis instance used by both Redis client and Celery.
- `TIMEZONE`: Default timezone for Celery and application-level scheduling.

## Local Development

1. **Create and activate a virtual environment**

    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    ```

2. **Install dependencies** (update `requirements.txt` as the project grows)

    ```bash
    pip install -U pip
    pip install flask flask-cors flask-sqlalchemy celery redis python-dotenv
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

## Next Step

The next development stage is to implement the core data models such as `User`, `Company`, and `Offer`, followed by their related services and API endpoints.
