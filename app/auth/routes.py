# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Authentication blueprint routes for registration, login, and profile retrieval."""

from __future__ import annotations

from http import HTTPStatus
from typing import Dict, Optional

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_

from .. import db
from ..models.user import User
from ..services.mailer import send_email, send_member_welcome_email
from ..services.notifications import send_welcome_notification
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


@auth_bp.post("/api/auth/register")
def register() -> tuple:
    """Register a new member account tailored for the mobile portal."""

    payload = _extract_json()
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


@auth_bp.route("/register/select", methods=["GET"])
def register_select_page() -> str:
    """Render the entry screen where visitors choose their account type."""

    return render_template("auth/register_select.html")


@auth_bp.route("/register/company", methods=["GET"])
def company_register_page() -> str:
    """Render the dedicated registration form for company accounts."""

    return render_template("auth/register_company.html")


@auth_bp.post("/api/auth/login")
def login() -> tuple:
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


@auth_bp.route("/login-page")
def login_page() -> str:
    """Render the browser-based login page."""

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET"])
def register_page() -> str:
    """Render the dedicated mobile-first registration screen for members."""

    return render_template("auth/register.html")


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

    response = redirect(url_for("auth.login_page"))
    response.delete_cookie("elite_token", path="/")
    response.headers["Clear-Site-Data"] = '"storage"'
    return response

