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
from typing import Dict, Optional, Tuple

from flask import (
    Blueprint,
    flash,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from sqlalchemy import or_

from .. import db
from ..models.user import User
from ..services.company_registration import register_company_account
from ..services.mailer import send_email, send_member_welcome_email
from ..services.notifications import send_welcome_notification
from ..forms import CompanyRegistrationForm
from .utils import confirm_token, create_token, decode_token, generate_token


auth_bp = Blueprint("auth", __name__)


def _extract_json() -> Dict[str, str]:
    """Return a JSON payload from the current request or an empty dict."""

    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    return {}


def _extract_bearer_token() -> Optional[str]:
    """Extract a bearer token from the Authorization header if present."""

    authorization = request.headers.get("Authorization", "").strip()
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


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

    db.session.add(user)
    db.session.commit()

    send_member_welcome_email(user=user)
    send_welcome_notification(user)

    token = create_token(user.id)

    response = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "membership_level": user.membership_level,
        "token": token,
        "redirect_url": url_for("portal.home"),
        "message": "User registered successfully.",
    }
    return jsonify(response), HTTPStatus.CREATED


@auth_bp.route("/api/auth/register", methods=["GET", "POST"], endpoint="api_register")
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


@auth_bp.route("/register/select", methods=["GET"], endpoint="register_select")
def register_select_page() -> Response:
    """Maintain legacy path by redirecting to the unified registration choice page."""

    return redirect(url_for("auth.register_choice"))


def _register_company_from_form(
    form: Optional[CompanyRegistrationForm] = None,
) -> Dict[str, str]:
    """Normalize HTML form submissions for company registration."""

    active_form = form or CompanyRegistrationForm()
    return {
        "company_name": (active_form.company_name.data or "").strip(),
        "description": (active_form.description.data or "").strip() or None,
        "email": (active_form.email.data or "").strip().lower(),
        "password": active_form.password.data,
        "username": "",
        "phone_number": (active_form.phone_number.data or "").strip(),
        "industry": (active_form.industry.data or "").strip(),
        "city": (active_form.city.data or "").strip(),
        "website_url": (active_form.website_url.data or "").strip(),
        "social_url": (active_form.social_url.data or "").strip(),
    }


@auth_bp.route("/register/member", methods=["GET", "POST"])
def register_member():
    """Render or process the member registration form for browser visitors."""

    if request.method == "GET":
        return render_template("auth/register.html")

    payload = request.get_json(silent=True) or {
        "username": (request.form.get("username") or "").strip(),
        "email": (request.form.get("email") or "").strip().lower(),
        "password": request.form.get("password"),
    }
    response, status = _register_member_from_payload(payload)

    if request.accept_mimetypes.accept_html and not request.is_json:
        if status == HTTPStatus.CREATED:
            data = response.get_json() if hasattr(response, "get_json") else None
            target = (data or {}).get("redirect_url") or url_for("portal.home")
            return redirect(target)
        return redirect(url_for("auth.register_member"))

    return response, status


@auth_bp.route("/auth/register/member", methods=["GET", "POST"])
def register_member_legacy():
    """Preserve the historic /auth/register/member path."""

    return register_member()


@auth_bp.route(
    "/register/company",
    methods=["GET", "POST"],
    endpoint="register_company",
)
def company_register_page():
    """Render or process the company registration form."""

    form = CompanyRegistrationForm()
    if request.method == "GET":
        return render_template("auth/register_company.html", form=form)

    if request.is_json:
        payload = request.get_json(silent=True) or {}
        result, status = register_company_account(payload)
        return jsonify(result), status

    if form.validate_on_submit():
        payload = _register_company_from_form(form)
        result, status = register_company_account(payload)
        if status == HTTPStatus.CREATED:
            flash("تم استلام طلبك وسيتم مراجعته من قبل الإدارة.", "success")
            return redirect(url_for("auth.register_company"))

        error_message = result.get("error") if isinstance(result, dict) else None
        if error_message:
            flash(error_message, "danger")
        return render_template("auth/register_company.html", form=form), status

    for field_errors in form.errors.values():
        for error in field_errors:
            flash(error, "danger")
    return render_template("auth/register_company.html", form=form), HTTPStatus.BAD_REQUEST


@auth_bp.post("/api/auth/login", endpoint="api_login")
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
        redirect_url = url_for("company_portal_bp.dashboard")
    elif user.role in {"admin", "superadmin"}:
        redirect_url = url_for("admin.dashboard_home")
    else:
        redirect_url = url_for("portal.home")
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


@auth_bp.get("/api/auth/profile")
def profile() -> tuple:
    """Return the authenticated user's profile details."""

    token = _extract_bearer_token()
    if not token:
        return (
            jsonify({"error": "Authorization header with Bearer token is required."}),
            HTTPStatus.UNAUTHORIZED,
        )

    try:
        user_id = decode_token(token)
    except ValueError as error:
        return jsonify({"error": str(error)}), HTTPStatus.UNAUTHORIZED

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


@auth_bp.route("/choose_membership")
def choose_membership() -> Response:
    """Preserve legacy path and forward visitors to the refreshed register chooser."""

    return redirect(url_for("auth.register_choice"))


@auth_bp.route("/login", methods=["GET"], endpoint="login")
@auth_bp.route("/login-page")
def login_page() -> str:
    """Render the browser-based login page."""

    logout_notice = session.pop("logout_notice", None)
    return render_template("auth/login.html", logout_notice=logout_notice)


@auth_bp.route("/register", methods=["GET"], endpoint="register_choice")
def register_choice() -> str:
    """عرض صفحة اختيار نوع التسجيل."""

    return render_template("auth/register_choice.html")


@auth_bp.route("/api/auth/verify/<token>")
def verify_email(token: str):
    """Activate a user account when the email confirmation token is valid."""

    # Decode the token to retrieve the email address embedded in the link.
    email = confirm_token(token)
    if not email:
        return jsonify({"message": "Invalid or expired token"}), HTTPStatus.BAD_REQUEST

    # Locate the user account associated with the confirmation email.
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_active:
        return jsonify({"message": "Account already verified"}), HTTPStatus.OK

    # Mark the account as active so the user can sign in going forward.
    user.is_active = True
    db.session.commit()
    return jsonify({"message": "Email verified successfully"}), HTTPStatus.OK


@auth_bp.route("/api/auth/reset-request", methods=["POST"])
def request_password_reset():
    """Send a password reset email containing a one-time token link."""

    data = request.get_json() or {}
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Email not found"}), HTTPStatus.NOT_FOUND

    # Issue a password reset token and deliver the reset instructions.
    token = generate_token(user.email)
    reset_url = f"{request.host_url}api/auth/reset-password/{token}"
    send_email(
        user.email,
        "Reset Your Elite Discounts Password",
        "emails/password_reset.html",
        {"reset_url": reset_url, "recipient_name": user.username or user.email},
    )
    return jsonify({"message": "Password reset email sent"}), HTTPStatus.OK


@auth_bp.route("/api/auth/reset-password/<token>", methods=["POST"])
def reset_password(token: str):
    """Persist a new password when the provided reset token is valid."""

    # Validate the token to extract the associated account email.
    email = confirm_token(token)
    if not email:
        return jsonify({"message": "Invalid or expired token"}), HTTPStatus.BAD_REQUEST

    data = request.get_json() or {}
    password = data.get("password")
    if not password:
        return (
            jsonify({"message": "Password is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Update the user's password with the provided credentials.
    user = User.query.filter_by(email=email).first_or_404()
    user.set_password(password)
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), HTTPStatus.OK


@auth_bp.route("/logout", methods=["GET", "POST"])
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

