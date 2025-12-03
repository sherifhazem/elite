# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.
# LINKED: Fixed duplicate email error after company deletion
# Ensures orphaned company owners are cleaned up before new company registration.
# LINKED: Added logout flow for member portal (no design change)
# Implements proper session termination and user redirect while preserving full mobile-first UI.
# LINKED: Route alignment & aliasing for registration and dashboards (no schema changes)
# Updated templates to use endpoint-based url_for; README cleaned & synced with actual routes.

"""Authentication blueprint routes for registration, login, and profile retrieval."""

from __future__ import annotations

from http import HTTPStatus
from functools import lru_cache
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple

from flask import (
    Blueprint,
    flash,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from sqlalchemy import or_

from flask_sqlalchemy import SQLAlchemy
from app.services.mailer import send_email, send_member_welcome_email
from app.modules.members.services.member_notifications_service import (
    send_welcome_notification,
)
from .utils import (
    confirm_token,
    create_token,
    decode_token,
    extract_bearer_token,
    generate_token,
)


auth = Blueprint(
    "auth",
    __name__,
    template_folder="../templates/members/auth",
    static_folder="../static/members",
)


if TYPE_CHECKING:  # pragma: no cover - used only for static analysis
    from app.models import User


WelcomeNotifier = Callable[["User"], Optional[int]]

_welcome_notifier_unavailable_logged = False


def _get_db() -> SQLAlchemy:
    """Safely retrieve the configured SQLAlchemy instance without importing app."""

    return current_app.extensions["sqlalchemy"]


def _get_user_model():
    """Return the User model without triggering circular imports at import time."""

    from app.models import User

    return User


@lru_cache(maxsize=1)
def _resolve_welcome_notifier() -> Optional[WelcomeNotifier]:
    """Return the welcome notification dispatcher when available."""

    try:  # pragma: no cover - optional dependency graph in some deployments
        from app.modules.members.services.member_notifications_service import (
            send_welcome_notification,
        )
    except Exception:
        return None

    if not callable(send_welcome_notification):
        return None

    return send_welcome_notification


def _extract_json() -> Dict[str, str]:
    """Return a JSON payload from the current request or an empty dict."""

    cleaned = getattr(request, "cleaned", {}) or {}
    return {k: v for k, v in cleaned.items() if not k.startswith("__")}


def _register_member_from_payload(payload: Dict[str, str]) -> Tuple[Response, int]:
    """Create a member account using the supplied payload values."""

    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")

    if not username or not email or not password:
        return (
            jsonify({"error": "username, email, and password are required."}),
            HTTPStatus.BAD_REQUEST,
        )

    User = _get_user_model()
    existing_user = User.query.filter(
        or_(User.username == username, User.email == email)
    ).first()
    if existing_user:
        return (
            jsonify({"error": "A user with that username or email already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    user = User(username=username, email=email)
    user.set_password(password)
    user.role = "member"
    user.membership_level = "Basic"
    user.is_active = True

    db = _get_db()
    db.session.add(user)
    db.session.commit()

    send_member_welcome_email(user=user)
    _dispatch_member_welcome_notification(user)

    token = create_token(user.id)

    response = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "membership_level": user.membership_level,
        "token": token,
        "redirect_url": url_for("portal.member_portal_home"),
        "message": "User registered successfully.",
    }
    return jsonify(response), HTTPStatus.CREATED


@auth.route("/api/auth/register", methods=["GET", "POST"], endpoint="api_register")
def register() -> Response | tuple:
    """Register a new member account tailored for the mobile portal."""

    if request.method == "GET":
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return (
                jsonify(
                    {
                        "message": "Submit a POST request with username, email, and password to register a new member.",
                        "redirect_url": url_for("auth.register_member"),
                    }
                ),
                HTTPStatus.OK,
            )

        return redirect(url_for("auth.register_member"))

    payload = _extract_json()
    return _register_member_from_payload(payload)


@auth.route("/register/select", methods=["GET"], endpoint="register_select")
def register_select_page() -> Response:
    """Maintain legacy path by redirecting to the unified registration choice page."""

    return redirect(url_for("auth.register_choice"))


@auth.route("/register/member", methods=["GET", "POST"], endpoint="register_member")
def register_member():
    """Render or process the member registration form for browser visitors."""

    if request.method == "GET":
        return render_template("members/auth/register.html")

    cleaned = getattr(request, "cleaned", {}) or {}
    payload = {
        "username": (cleaned.get("username") or "").strip(),
        "email": (cleaned.get("email") or "").strip().lower(),
        "password": cleaned.get("password"),
    }
    response, status = _register_member_from_payload(payload)

    if request.accept_mimetypes.accept_html and not request.is_json:
        if status == HTTPStatus.CREATED:
            data = response.get_json() if hasattr(response, "get_json") else None
            target = (data or {}).get("redirect_url") or url_for("portal.member_portal_home")
            return redirect(target)
        return redirect(url_for("auth.register_member"))

    return response, status


@auth.route(
    "/auth/register/member", methods=["GET", "POST"], endpoint="register_member_legacy"
)
def register_member_legacy():
    """Preserve the historic /auth/register/member path."""

    return register_member()


@auth.post("/api/auth/login", endpoint="api_login")
def api_login() -> tuple:
    """Authenticate a user and return a signed JWT token."""

    payload = _extract_json()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")

    if not email or not password:
        return (
            jsonify({"error": "email and password are required."}),
            HTTPStatus.BAD_REQUEST,
        )

    User = _get_user_model()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return (
            jsonify({"error": "Invalid credentials."}),
            HTTPStatus.UNAUTHORIZED,
        )

    if not user.is_active:
        return (
            jsonify({"error": "Account is inactive. Please contact support."}),
            HTTPStatus.FORBIDDEN,
        )

    token = create_token(user.id)
    if user.role == "company":
        redirect_url = url_for("company_portal.company_dashboard_overview")
    elif user.role in {"admin", "superadmin"}:
        redirect_url = url_for("admin.dashboard_home")
    else:
        redirect_url = url_for("portal.member_portal_home")
    return (
        jsonify(
            {
                "token": token,
                "token_type": "Bearer",
                "role": user.role,
                "is_active": user.is_active,
                "redirect_url": redirect_url,
            }
        ),
        HTTPStatus.OK,
    )


@auth.get("/api/auth/profile", endpoint="profile")
def profile() -> tuple:
    """Return the authenticated user's profile details."""

    token = extract_bearer_token(request.headers.get("Authorization", ""))
    if not token:
        return (
            jsonify({"error": "Authorization header with Bearer token is required."}),
            HTTPStatus.UNAUTHORIZED,
        )

    try:
        user_id = decode_token(token)
    except ValueError as error:
        return jsonify({"error": str(error)}), HTTPStatus.UNAUTHORIZED

    User = _get_user_model()
    user = User.query.get(user_id)
    if user is None:
        return (
            jsonify({"error": "User not found."}),
            HTTPStatus.NOT_FOUND,
        )

    response = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "joined_at": user.joined_at.isoformat() if user.joined_at else None,
    }
    return jsonify(response), HTTPStatus.OK


@auth.route("/choose_membership", endpoint="choose_membership")
def choose_membership() -> Response:
    """Preserve legacy path and forward visitors to the refreshed register chooser."""

    return redirect(url_for("auth.register_choice"))


@auth.route("/login", methods=["GET"], endpoint="login")
@auth.route("/login-page", endpoint="login_page")
def login_page() -> str:
    """Render the browser-based login page."""

    logout_notice = session.pop("logout_notice", None)
    return render_template("members/auth/login.html", logout_notice=logout_notice)


@auth.route("/register", methods=["GET"], endpoint="register_choice")
def register_choice() -> str:
    """عرض صفحة اختيار نوع التسجيل."""

    return render_template("members/auth/register_choice.html")


@auth.route("/api/auth/verify/<token>", endpoint="verify_email")
def verify_email(token: str):
    """Activate a user account when the email confirmation token is valid."""

    # Decode the token to retrieve the email address embedded in the link.
    email = confirm_token(token)
    if not email:
        return jsonify({"message": "Invalid or expired token"}), HTTPStatus.BAD_REQUEST

    # Locate the user account associated with the confirmation email.
    User = _get_user_model()
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_active:
        return jsonify({"message": "Account already verified"}), HTTPStatus.OK

    # Mark the account as active so the user can sign in going forward.
    user.is_active = True
    db = _get_db()
    db.session.commit()
    return jsonify({"message": "Email verified successfully"}), HTTPStatus.OK


@auth.route("/api/auth/reset-request", methods=["POST"], endpoint="request_password_reset")
def request_password_reset():
    """Send a password reset email containing a one-time token link."""

    data = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    email = data.get("email")
    User = _get_user_model()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Email not found"}), HTTPStatus.NOT_FOUND

    # Issue a password reset token and deliver the reset instructions.
    token = generate_token(user.email)
    reset_url = f"{request.host_url}api/auth/reset-password/{token}"
    send_email(
        user.email,
        "Reset Your Elite Discounts Password",
        "core/emails/password_reset.html",
        {"reset_url": reset_url, "recipient_name": user.username or user.email},
    )
    return jsonify({"message": "Password reset email sent"}), HTTPStatus.OK


@auth.route(
    "/api/auth/reset-password/<token>",
    methods=["POST"],
    endpoint="reset_password",
)
def reset_password(token: str):
    """Persist a new password when the provided reset token is valid."""

    # Validate the token to extract the associated account email.
    email = confirm_token(token)
    if not email:
        return jsonify({"message": "Invalid or expired token"}), HTTPStatus.BAD_REQUEST

    data = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    password = data.get("password")
    if not password:
        return (
            jsonify({"message": "Password is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Update the user's password with the provided credentials.
    User = _get_user_model()
    user = User.query.filter_by(email=email).first_or_404()
    user.set_password(password)
    db = _get_db()
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), HTTPStatus.OK


@auth.route("/logout", methods=["GET", "POST"], endpoint="logout")
def logout():
    """Clear stored authentication state and return to the login screen."""

    session.clear()
    session["logout_notice"] = "تم تسجيل الخروج بنجاح"

    response = redirect(url_for("auth.login_page"))
    response.delete_cookie("elite_token", path="/")
    response.headers["Clear-Site-Data"] = '"storage"'
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@auth.get("/register/company")
def legacy_company_register_redirect():
    """Redirect legacy company registration URLs to the new company blueprint."""

    return redirect(url_for("company.register_company"))


def _dispatch_member_welcome_notification(user: "User") -> None:
    """Safely send welcome notification when available."""

    notifier = _resolve_welcome_notifier()
    if notifier is None:
        return

    try:
        notifier(user)
    except Exception:  # pragma: no cover - notifications are best-effort
        pass

