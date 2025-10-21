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

from datetime import datetime
from http import HTTPStatus
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

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
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.company import Company
from ..models.user import User
from ..services.mailer import send_email, send_member_welcome_email
from ..services.notifications import queue_notification, push_admin_notification
from ..forms import CITY_CHOICES, INDUSTRY_CHOICES, CompanyRegistrationForm
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


@auth_bp.post("/api/auth/register")
def register() -> tuple:
    """Register a new member account tailored for the mobile portal."""

    payload = _extract_json()
    return _register_member_from_payload(payload)


@auth_bp.route("/register/select", methods=["GET"], endpoint="register_select")
def register_select_page() -> str:
    """Render the entry screen where visitors choose their account type."""

    return render_template("auth/register_select.html")


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


def _register_company_from_payload(payload: Dict[str, str]) -> Tuple[Response, int]:
    """Create a company account alongside its owner using the payload."""

    requested_username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    company_name = (payload.get("company_name") or "").strip()
    description = payload.get("description")
    phone_number = (payload.get("phone_number") or "").strip()
    industry = (payload.get("industry") or "").strip()
    city = (payload.get("city") or "").strip()
    website_url = (payload.get("website_url") or "").strip()
    social_url = (payload.get("social_url") or "").strip()

    if not email or not password or not company_name:
        return (
            jsonify(
                {
                    "error": "email, password, and company_name are required.",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    if not phone_number or len(phone_number) < 8:
        return (
            jsonify({"error": "A valid phone_number with at least 8 characters is required."}),
            HTTPStatus.BAD_REQUEST,
        )

    allowed_industries = {choice for choice, _ in INDUSTRY_CHOICES if choice}
    allowed_cities = {choice for choice, _ in CITY_CHOICES if choice}
    if industry not in allowed_industries:
        return (
            jsonify({"error": "industry is required and must be a supported choice."}),
            HTTPStatus.BAD_REQUEST,
        )
    if city not in allowed_cities:
        return (
            jsonify({"error": "city is required and must be a supported choice."}),
            HTTPStatus.BAD_REQUEST,
        )

    def _is_valid_url(value: str) -> bool:
        if not value:
            return False
        parsed = urlparse(value)
        return bool(parsed.scheme in {"http", "https"} and parsed.netloc)

    if website_url and not _is_valid_url(website_url):
        return (
            jsonify({"error": "website_url must be a valid HTTP or HTTPS link."}),
            HTTPStatus.BAD_REQUEST,
        )
    if not social_url or not _is_valid_url(social_url):
        return (
            jsonify({"error": "social_url must be a valid HTTP or HTTPS link."}),
            HTTPStatus.BAD_REQUEST,
        )

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        normalized_role = (existing_user.role or "").strip().lower()
        associated_company_exists = False
        if existing_user.company_id:
            associated_company_exists = (
                Company.query.filter_by(id=existing_user.company_id).first()
                is not None
            )
        owns_company = (
            Company.query.filter_by(owner_user_id=existing_user.id).first()
            is not None
        )

        if (
            normalized_role == "company"
            and not associated_company_exists
            and not owns_company
        ):
            current_app.logger.info(
                "Removed orphaned company user before re-registering the company.",
                extra={"email": existing_user.email},
            )
            db.session.delete(existing_user)
            db.session.flush()
        else:
            return (
                jsonify({"error": "A user with the provided email already exists."}),
                HTTPStatus.BAD_REQUEST,
            )

    if Company.query.filter_by(name=company_name).first():
        return (
            jsonify({"error": "A company with the provided name already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    def _generate_username() -> str:
        """Derive a unique username for the company owner when not provided."""

        import re

        base_source = requested_username or company_name or email.split("@")[0]
        cleaned = re.sub(r"[^\w\u0621-\u064A]+", "", base_source, flags=re.UNICODE)
        cleaned = cleaned or "company"
        candidate = cleaned
        suffix = 1
        while User.query.filter_by(username=candidate).first():
            candidate = f"{cleaned}{suffix}"
            suffix += 1
        return candidate

    username = requested_username or _generate_username()

    if requested_username and User.query.filter_by(username=username).first():
        return (
            jsonify({"error": "A user with the provided username already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    company = Company(name=company_name, description=description)
    company.status = "pending"
    company.admin_notes = None

    owner = User(username=username, email=email)
    owner.set_password(password)
    owner.role = "company"
    owner.membership_level = "Basic"
    owner.is_active = False

    company.owner = owner
    owner.company = company
    company.notification_preferences = {
        "contact_phone": phone_number,
        "industry": industry,
        "city": city,
        "website_url": website_url or None,
        "social_url": social_url,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
    }

    db.session.add(owner)
    db.session.add(company)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify({"error": "Unable to register company with the provided details."}),
            HTTPStatus.BAD_REQUEST,
        )

    push_admin_notification(
        event_type="company.new_application",
        title="New Company Application",
        message=f"A new company '{company.name}' submitted an application.",
        link="/admin/companies?status=pending",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    _notify_admin_of_company_request(
        company=company,
        owner=owner,
        phone_number=phone_number,
        industry=industry,
        city=city,
    )

    response = {
        "company": {
            "id": company.id,
            "name": company.name,
            "description": company.description,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        },
        "owner": {
            "id": owner.id,
            "username": owner.username,
            "email": owner.email,
            "role": owner.role,
            "is_active": owner.is_active,
        },
        "message": "Company registration request received and pending review.",
        "redirect_url": url_for("auth.login_page"),
    }
    return jsonify(response), HTTPStatus.CREATED


def _notify_admin_of_company_request(
    *,
    company: Company,
    owner: User,
    phone_number: str,
    industry: str,
    city: str,
) -> None:
    """Send admin notifications and email summarizing the company request."""

    admin_users = (
        User.query.filter(
            User.role.in_(["admin", "superadmin"]),
            User.is_active.is_(True),
        )
        .order_by(User.id)
        .all()
    )

    if not admin_users:
        current_app.logger.warning(
            "Company registration pending but no admin recipients found.",
            extra={"company_id": company.id},
        )
    else:
        message = (
            f"تم استلام طلب تسجيل شركة جديدة: {company.name}.\n"
            f"المدينة: {city}.\n"
            f"المجال: {industry}.\n"
            f"رقم التواصل: {phone_number}."
        )
        metadata = {
            "company_id": company.id,
            "company_name": company.name,
            "industry": industry,
            "city": city,
            "phone_number": phone_number,
            "owner_id": owner.id,
            "owner_email": owner.email,
        }
        for admin in admin_users:
            queue_notification(
                admin.id,
                type="new_company_request",
                title="طلب تسجيل شركة جديد",
                message=message,
                metadata=metadata,
            )

    admin_email = (
        current_app.config.get("ADMIN_CONTACT_EMAIL")
        or current_app.config.get("MAIL_DEFAULT_SENDER")
        or current_app.config.get("MAIL_USERNAME")
    )
    if not admin_email:
        return

    subject = f"طلب تسجيل شركة جديد: {company.name}"
    message_lines = [
        f"اسم الشركة: {company.name}",
        f"المدينة: {city}",
        f"المجال: {industry}",
        f"البريد المسؤول: {owner.email}",
        f"رقم الجوال: {phone_number}",
        f"رابط التواصل: {company.notification_preferences.get('social_url')}",
    ]
    if company.notification_preferences.get("website_url"):
        message_lines.append(
            f"الموقع الإلكتروني: {company.notification_preferences.get('website_url')}"
        )
    message_lines.append("الحالة الحالية: Pending Review")

    message_html = "<br>".join(message_lines)
    context = {"subject": subject, "message_html": message_html}
    send_email(admin_email, subject, "emails/admin_broadcast.html", context)


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
        return _register_company_from_payload(payload)

    if form.validate_on_submit():
        payload = _register_company_from_form(form)
        response, status = _register_company_from_payload(payload)
        if status == HTTPStatus.CREATED:
            flash("تم استلام طلبك وسيتم مراجعته من قبل الإدارة.", "success")
            return redirect(url_for("auth.register_company"))

        error_payload = response.get_json() if hasattr(response, "get_json") else None
        if error_payload and error_payload.get("error"):
            flash(error_payload["error"], "danger")
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


@auth_bp.route("/login", methods=["GET"], endpoint="login")
@auth_bp.route("/login-page")
def login_page() -> str:
    """Render the browser-based login page."""

    logout_notice = session.pop("logout_notice", None)
    return render_template("auth/login.html", logout_notice=logout_notice)


@auth_bp.route("/register", methods=["GET", "POST"])
def register_page():
    """Legacy alias preserved for older registration bookmarks."""

    if request.method == "POST":
        return register_member()
    return redirect(url_for("auth.register_member"))


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

