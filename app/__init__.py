# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""
# FIXED: Unified context processor to ensure role and logout visibility across Flask-Login and JWT sessions.
# - Added 'role' key for compatibility with templates.
# - Forced is_authenticated=True for JWT-based users.
# - Ensured user_status_label and logout button visibility are consistent.

from http import HTTPStatus
from flask import Flask, abort, g, request
from flask_login import LoginManager, current_user as flask_login_current_user
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from celery import Celery
from redis import Redis
# ======================================================
# Scoped CSRF Protection — applies only to form routes
# ======================================================
from flask_wtf.csrf import CSRFProtect

from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]

CORS(app, resources={r"/api/*": {"origins": "*"}})

if app.config.get("RELAX_SECURITY_CONTROLS", False):
    class _DisabledCSRF:
        """No-op CSRF handler used while protections are relaxed during development."""

        @staticmethod
        def exempt(view_func):
            return view_func

    csrf = _DisabledCSRF()
    app.logger.warning("CSRF protection disabled for development and testing purposes.")
else:
    csrf = CSRFProtect()
    csrf.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
redis_client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)

celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

mail = Mail(app)

# Ensure models are registered
from .models import Company, Offer, Permission, Redemption, User  # noqa: F401

# Register blueprints after extensions
from .routes import (
    companies,
    main as main_blueprint,
    notifications,
    offers,
    redemption,
    users,
)
from .routes.user_portal_routes import portal  # noqa: E402
from .auth import auth  # noqa: E402
from .admin import admin  # noqa: E402
from .company import company_portal  # noqa: E402

# JWT authentication temporarily disabled during web testing phase.
# To re-enable, restore imports from flask_jwt_extended.
# from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request_optional
get_jwt_identity = lambda: None
verify_jwt_in_request_optional = lambda *a, **kw: None

@login_manager.user_loader
def load_user(user_id: str):
    """Load a persisted user session for Flask-Login."""

    from .models import User

    return User.query.get(int(user_id))


@app.before_request
def attach_current_user() -> None:
    """Resolve the current user from JWT credentials and guard protected areas."""
    from .services.roles import resolve_user_from_request

    current = resolve_user_from_request()
    g.current_user = current
    normalized_role = "guest"

    if current is not None:
        normalized_role = (getattr(current, "role", "member") or "member").strip().lower()
        # ضمان وجود خاصية is_authenticated
        if getattr(current, "is_authenticated", None) is not True:
            try:
                current.is_authenticated = True
            except AttributeError:
                pass

    g.user_role = normalized_role
    g.user_permissions = getattr(current, "permissions", None) if current else None

    if not app.config.get("RELAX_SECURITY_CONTROLS", False):
        protected_paths = ("/admin", "/company")
        exempt_paths = (
            "/",                          # homepage
            "/auth/login",                # login
            "/auth/register",             # register
            "/company/complete_registration",  # correction/completion link
            "/static",                    # static files
            "/api",                       # public APIs
        )

        if request.path.startswith(protected_paths) and not any(
            request.path.startswith(ex) for ex in exempt_paths
        ):
            if g.current_user is None:
                abort(HTTPStatus.UNAUTHORIZED)
            if hasattr(g.current_user, "is_active") and not g.current_user.is_active:
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
            except Exception:
                identity = None
            if identity and not user:
                fetched_user = User.query.get(identity)
                if fetched_user:
                    # تأكد من أن المستخدم قابل للعرض في القوالب
                    try:
                        fetched_user.is_authenticated = True
                    except AttributeError:
                        pass
                    user = fetched_user
                    role = getattr(fetched_user, "role", "member") or "member"
                    permissions = getattr(fetched_user, "permissions", None)
                    username = getattr(fetched_user, "username", username)

    normalized_role = (role or "guest").strip().lower()
    g.current_user = user
    g.user_role = normalized_role
    g.user_permissions = permissions

    if user:
        if getattr(user, "is_authenticated", None) is not True:
            try:
                user.is_authenticated = True
            except AttributeError:
                pass
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
        "role": normalized_role,  # <--- أُضيف لضمان عمل {{ role }} في القوالب
        "user_role": normalized_role,
        "user_permissions": permissions,
        "user_status_label": user_status_label,
        "is_admin": is_admin,
        "is_superadmin": is_superadmin,
    }


app.logger.info("✅ Database connection configured for %s", app.config["SQLALCHEMY_DATABASE_URI"])
# Register blueprints
app.register_blueprint(main_blueprint)
app.register_blueprint(admin)  # ← الآن يستخدم تعريف blueprint الصحيح من app/admin/__init__.py
app.register_blueprint(auth)
app.register_blueprint(company_portal)
app.register_blueprint(portal)
app.register_blueprint(offers, url_prefix="/api/offers")
app.register_blueprint(companies, url_prefix="/api/companies")
app.register_blueprint(users, url_prefix="/api/users")
app.register_blueprint(redemption)
app.register_blueprint(notifications)

