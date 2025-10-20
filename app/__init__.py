# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""

# LINKED: Fixed user context processor to inject current_user and role for both Flask-Login and JWT sessions.
# Ensures consistent visibility of role-based UI elements (Logout, Admin links, etc.).

from http import HTTPStatus

from flask import Flask, abort, g, request
from flask_login import current_user as flask_login_current_user
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

try:  # pragma: no cover - optional dependency integration
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request_optional
except ImportError:  # pragma: no cover - gracefully degrade when extension missing
    get_jwt_identity = None
    verify_jwt_in_request_optional = None

PROTECTED_PREFIXES = ("/admin", "/company")


@app.before_request
def attach_current_user() -> None:
    """Resolve the current user from JWT credentials and guard protected areas."""

    from .services.roles import resolve_user_from_request

    current = resolve_user_from_request()
    g.current_user = current
    normalized_role = "guest"
    if current is not None:
        normalized_role = (getattr(current, "role", "member") or "member").strip().lower()
    g.user_role = normalized_role
    g.user_permissions = getattr(current, "permissions", None) if current else None

    if request.path.startswith(PROTECTED_PREFIXES):
        if g.current_user is None:
            abort(HTTPStatus.UNAUTHORIZED)
        if not g.current_user.is_active:
            abort(HTTPStatus.FORBIDDEN)


@app.context_processor
def inject_user_context():
    """Inject user and role context into all templates, including status labels."""

    user = getattr(g, "current_user", None)
    role = getattr(g, "user_role", "guest") or "guest"
    permissions = getattr(g, "user_permissions", None)
    username = "ضيف"

    if user and getattr(user, "is_authenticated", False):
        role = getattr(user, "role", role) or role
        username = getattr(user, "username", username)
    else:
        if getattr(flask_login_current_user, "is_authenticated", False):
            user = flask_login_current_user
            role = getattr(user, "role", "member") or "member"
            permissions = getattr(user, "permissions", None)
            username = getattr(user, "username", username)
        elif verify_jwt_in_request_optional and get_jwt_identity:
            try:
                verify_jwt_in_request_optional()
                identity = get_jwt_identity()
            except Exception:  # pragma: no cover - JWT extension raises for bad tokens
                identity = None
            if identity and not user:
                fetched_user = User.query.get(identity)
                if fetched_user:
                    user = fetched_user
                    role = getattr(fetched_user, "role", "member") or "member"
                    permissions = getattr(fetched_user, "permissions", None)
                    username = getattr(fetched_user, "username", username)

    normalized_role = (role or "guest").strip().lower()
    g.current_user = user
    g.user_role = normalized_role
    g.user_permissions = permissions

    if user:
        if normalized_role == "superadmin":
            user_status_label = f"🔑 Superadmin ({username})"
        elif normalized_role == "admin":
            user_status_label = f"🛡 Admin ({username})"
        elif normalized_role == "company":
            user_status_label = f"🏢 {username} (شركة)"
        else:
            user_status_label = f"👤 {username}"
    else:
        user_status_label = "👥 تصفح كـ ضيف"

    is_admin = normalized_role in {"admin", "superadmin"}
    is_superadmin = normalized_role == "superadmin"

    return {
        "current_user": user,
        "user_role": normalized_role,
        "user_permissions": permissions,
        "user_status_label": user_status_label,
        "is_admin": is_admin,
        "is_superadmin": is_superadmin,
    }


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
