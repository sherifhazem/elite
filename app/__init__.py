# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""
# FIXED: Unified context processor to ensure role and logout visibility across Flask-Login and JWT sessions.
# - Added 'role' key for compatibility with templates.
# - Forced is_authenticated=True for JWT-based users.
# - Ensured user_status_label and logout button visibility are consistent.

import os
from http import HTTPStatus
from flask import Flask, abort, g, request
from flask_login import current_user as flask_login_current_user
from flask_cors import CORS
from redis import Redis
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.middleware.shared_data import SharedDataMiddleware

from .config import Config
from app.core.database import db
from app.core.extensions import celery, csrf, login_manager, mail, migrate
from app.core.central_middleware import register_central_middleware
from app.logging.logger import initialize_logging

redis_client: Redis | None = None


# JWT authentication temporarily disabled during web testing phase.
# To re-enable, restore imports from flask_jwt_extended.
get_jwt_identity = lambda: None
verify_jwt_in_request_optional = lambda *a, **kw: None


def _mount_static_mappings(app: Flask) -> None:
    """Serve module-specific static assets through the shared /static endpoint."""

    static_roots = {
        "admin": os.path.join(app.root_path, "modules", "admin", "static", "admin"),
        "companies": os.path.join(app.root_path, "modules", "companies", "static", "companies"),
        "members": os.path.join(app.root_path, "modules", "members", "static", "members"),
        "core": os.path.join(app.root_path, "core", "static"),
    }

    mounts: dict[str, str] = {}
    for module_key in ("admin", "companies", "members"):
        module_path = static_roots[module_key]
        if os.path.isdir(module_path):
            mounts[f"/static/{module_key}"] = module_path

    core_static = static_roots.get("core")
    if core_static and os.path.isdir(core_static):
        mounts["/static"] = core_static

    if mounts:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, mounts)


def _enforce_security_requirements(app: Flask) -> None:
    """Fail fast when mandatory security controls are missing."""

    secret_key = app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is required and cannot be empty during startup.")

    if app.config.get("RELAX_SECURITY_CONTROLS"):
        raise RuntimeError("RELAX_SECURITY_CONTROLS cannot be enabled during application startup.")

    if not app.config.get("WTF_CSRF_ENABLED", True):
        raise RuntimeError("CSRF protection must remain enabled; startup aborted.")


def _validate_production_settings(app: Flask) -> None:
    """Ensure required environment values are set in production environments."""

    env_name = str(app.config.get("ENV", "production")).lower()
    if env_name != "production":
        return

    required_keys = {
        "SECRET_KEY": "Application secret key is required in production.",
        "SQLALCHEMY_DATABASE_URI": "Database connection string is required in production.",
        "MAIL_SERVER": "MAIL_SERVER must be configured in production.",
        "MAIL_USERNAME": "MAIL_USERNAME must be configured in production.",
        "MAIL_PASSWORD": "MAIL_PASSWORD must be configured in production.",
    }

    missing = [key for key, message in required_keys.items() if not app.config.get(key)]
    if missing:
        error_messages = [required_keys[key] for key in missing]
        raise RuntimeError(" | ".join(error_messages))


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, template_folder="core/templates", static_folder="core/static")
    app.config.from_object(config_class)

    _enforce_security_requirements(app)
    _validate_production_settings(app)

    app.secret_key = app.config["SECRET_KEY"]

    initialize_logging(app)

    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(os.path.join(app.root_path, "modules", "members", "templates")),
            FileSystemLoader(os.path.join(app.root_path, "modules", "companies", "templates")),
            FileSystemLoader(os.path.join(app.root_path, "modules", "admin", "templates")),
            app.jinja_loader,
        ]
    )

    _mount_static_mappings(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    register_central_middleware(app)

    csrf_extension = csrf
    if app.config.get("RELAX_SECURITY_CONTROLS", False):
        class _DisabledCSRF:
            """No-op CSRF handler used while protections are relaxed during development."""

            @staticmethod
            def exempt(view_func):
                return view_func

        csrf_extension = _DisabledCSRF()
    else:
        csrf_extension.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)

    global redis_client
    redis_client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)

    celery.conf.update(app.config)
    celery.conf.broker_url = app.config.get("CELERY_BROKER_URL", celery.conf.broker_url)
    celery.conf.result_backend = app.config.get("CELERY_RESULT_BACKEND", celery.conf.result_backend)

    class AppContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = AppContextTask

    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        """Load a persisted user session for Flask-Login."""

        from app.models import User

        return User.query.get(int(user_id))

    from app.services.access_control import resolve_user_from_request
    from app.modules.members.auth.utils import (
        AUTH_COOKIE_NAME,
        clear_auth_cookie,
        create_token,
        set_auth_cookie,
    )

    @app.before_request
    def attach_current_user() -> None:
        """Resolve the current user from JWT credentials and guard protected areas."""

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

    @app.after_request
    def refresh_auth_cookie(response):
        """Renew the authentication cookie on each authenticated request."""

        user = getattr(g, "current_user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            if request.cookies.get(AUTH_COOKIE_NAME):
                token = create_token(user.id)
                set_auth_cookie(response, token)
        elif request.endpoint == "auth.logout":
            clear_auth_cookie(response)
        return response

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
                    from app.models import User

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

    with app.app_context():
        from app.models import Company, Offer, Permission, Redemption, User  # noqa: F401

    from app.modules.members.routes import (
        main as main_blueprint,
        notifications,
        offers,
        redemption,
        usage_codes,
        users,
    )
    from app.modules.members.routes.user_portal_routes import portal  # noqa: E402
    from app.modules.members.auth.routes import auth  # noqa: E402
    from app.modules.companies.routes import company_bp  # noqa: E402
    from app.modules.admin import admin  # noqa: E402
    from app.modules.companies import company_portal  # noqa: E402
    from app.modules.companies.routes.api_routes import companies  # noqa: E402
    from routes.dev_tools.normalization_test import normalization_test  # noqa: E402
    from routes.dev_tools.choices_monitor import choices_monitor  # noqa: E402

    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin)  # ← الآن يستخدم تعريف blueprint الصحيح من app/admin/__init__.py
    app.register_blueprint(auth)
    app.register_blueprint(company_bp)
    app.register_blueprint(company_portal)
    app.register_blueprint(portal)
    app.register_blueprint(offers, url_prefix="/api/offers")
    app.register_blueprint(companies, url_prefix="/api/companies")
    app.register_blueprint(users, url_prefix="/api/users")
    app.register_blueprint(redemption)
    app.register_blueprint(usage_codes)
    app.register_blueprint(notifications)

    env_name = str(app.config.get("ENV", "production")).lower()
    if env_name != "production":
        app.register_blueprint(normalization_test)
        app.register_blueprint(choices_monitor)

    return app
