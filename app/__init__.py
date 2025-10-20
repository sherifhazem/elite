# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""

from http import HTTPStatus

from flask import Flask, abort, g, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
from redis import Redis

from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]

CORS(app, resources={r"/api/*": {"origins": "*"}})

db = SQLAlchemy(app)
migrate = Migrate(app, db)

redis_client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)

celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Ensure models are registered with SQLAlchemy's metadata for migrations
from .models import Company, Offer, Permission, Redemption, User  # noqa: F401

# Register blueprints after extensions are initialized
from .routes import (  # noqa: E402
    company_routes,
    main as main_blueprint,
    notif_bp,
    offer_routes,
    redemption_bp,
    user_routes,
)
from .routes.user_portal_routes import portal_bp  # noqa: E402
from .auth import auth_bp  # noqa: E402
from .admin import admin_bp  # noqa: E402
from .admin.routes_reports import reports_bp  # noqa: E402
from .company import company_portal_bp  # noqa: E402

PROTECTED_PREFIXES = ("/admin", "/company")


@app.before_request
def attach_current_user() -> None:
    """Resolve the current user from JWT credentials and guard protected areas."""

    from .services.roles import resolve_user_from_request

    g.current_user = resolve_user_from_request()
    if request.path.startswith(PROTECTED_PREFIXES):
        if g.current_user is None:
            abort(HTTPStatus.UNAUTHORIZED)
        if not g.current_user.is_active:
            abort(HTTPStatus.FORBIDDEN)


@app.context_processor
def inject_current_user():
    """Expose the current user to templates for role-aware rendering."""

    return {"current_user": getattr(g, "current_user", None)}


app.logger.info("✅ Database connection configured for %s", app.config["SQLALCHEMY_DATABASE_URI"])

app.register_blueprint(main_blueprint)
app.register_blueprint(user_routes, url_prefix="/api/users")
app.register_blueprint(company_routes, url_prefix="/api/companies")
app.register_blueprint(offer_routes, url_prefix="/api/offers")
app.register_blueprint(notif_bp)
app.register_blueprint(redemption_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(portal_bp)
app.register_blueprint(company_portal_bp)
