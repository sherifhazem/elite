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
from flask_login import current_user, login_user
from sqlalchemy import or_

from flask_sqlalchemy import SQLAlchemy
from app.services.mailer import send_email, send_member_welcome_email
from app.modules.members.services.member_notifications_service import (
    send_welcome_notification,
)
from app.services.sms_service import SMSService
from .utils import (
    AUTH_COOKIE_NAME,
    clear_auth_cookie,
    confirm_token,
    create_token,
    decode_token,
    extract_bearer_token,
    generate_token,
    set_auth_cookie,
)
from app.core.extensions import csrf


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
    phone = (payload.get("phone") or "").strip()
    password = payload.get("password")

    if not username or not phone or not password:
        return (
            jsonify({"error": "الاسم ورقم الجوال وكلمة المرور مطلوبة."}),
            HTTPStatus.BAD_REQUEST,
        )

    User = _get_user_model()
    # Check if username or phone already exists
    existing_user = User.query.filter(
        or_(User.username == username, User.phone_number == phone)
    ).first()
    
    if existing_user:
        return (
            jsonify({"error": "اسم المستخدم أو رقم الجوال مسجل مسبقاً."}),
            HTTPStatus.BAD_REQUEST,
        )

    user = User(username=username, phone_number=phone)
    user.set_password(password)
    user.role = "member"
    user.is_active = True # Active but phone not verified yet
    user.is_phone_verified = False

    db = _get_db()
    db.session.add(user)
    db.session.commit()

    # Send OTP
    sms_service = SMSService()
    sms_service.send_otp(phone, purpose='registration')

    response = {
        "id": user.id,
        "username": user.username,
        "phone": user.phone_number,
        "role": user.role,
        "redirect_url": url_for("auth.verify_otp_page", phone=phone),
        "message": "تم التسجيل بنجاح. يرجى التحقق من رقم الجوال.",
    }
    return jsonify(response), HTTPStatus.CREATED


@auth.route("/api/auth/register", methods=["GET", "POST"], endpoint="api_register")
@csrf.exempt
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
        "phone": (cleaned.get("phone") or "").strip(),
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


@auth.route("/auth/register/member", methods=["GET", "POST"], endpoint="register_member_legacy")
def register_member_legacy():
    """Preserve the historic /auth/register/member path."""

    return register_member()


@auth.route("/verify-otp", methods=["GET"], endpoint="verify_otp_page")
def verify_otp_page():
    """Render the OTP verification page."""
    phone = request.args.get('phone')
    if not phone:
        return redirect(url_for('auth.register_member'))
    return render_template("members/auth/verify_otp.html", phone_number=phone)


@auth.post("/api/auth/verify-otp", endpoint="api_verify_otp")
@csrf.exempt
def api_verify_otp():
    """Verify the submitted OTP code."""
    payload = _extract_json()
    phone = payload.get('phone')
    code = payload.get('code')

    if not phone or not code:
        return jsonify({"message": "رقم الجوال والرمز مطلوبان."}), HTTPStatus.BAD_REQUEST

    sms_service = SMSService()
    if sms_service.verify_otp(phone, code, purpose='registration'):
        User = _get_user_model()
        user = User.query.filter_by(phone_number=phone).first()
        if user:
            user.is_phone_verified = True
            db = _get_db()
            db.session.commit()
            
            # Send welcome SMS
            sms_service.send_welcome(phone)
            
            # Auto login after verification
            login_user(user)
            token = create_token(user.id)
            response = jsonify({
                "message": "تم التحقق بنجاح.",
                "redirect_url": url_for("portal.member_portal_home"),
                "token": token
            })
            set_auth_cookie(response, token)
            return response, HTTPStatus.OK
            
        return jsonify({"message": "المستخدم غير موجود."}), HTTPStatus.NOT_FOUND
    
    return jsonify({"message": "الرمز غير صحيح أو منتهي الصلاحية."}), HTTPStatus.BAD_REQUEST


@auth.post("/api/auth/resend-otp", endpoint="api_resend_otp")
@csrf.exempt
def api_resend_otp():
    """Resend a new OTP to the user's phone."""
    payload = _extract_json()
    phone = payload.get('phone')
    if not phone:
        return jsonify({"message": "رقم الجوال مطلوب."}), HTTPStatus.BAD_REQUEST

    sms_service = SMSService()
    sms_service.send_otp(phone, purpose='registration')
    return jsonify({"message": "تم إرسال الرمز بنجاح."}), HTTPStatus.OK


@auth.route("/link-phone", methods=["GET"], endpoint="link_phone_page")
def link_phone_page():
    """Render the phone linking page for legacy users."""
    user_id = request.args.get('id')
    if not user_id:
        return redirect(url_for('auth.login'))
    return render_template("members/auth/link_phone.html", user_id=user_id)


@auth.post("/api/auth/link-phone", endpoint="api_link_phone")
@csrf.exempt
def api_link_phone():
    """Link a phone number to an existing user account."""
    payload = _extract_json()
    user_id = payload.get('user_id')
    phone = payload.get('phone')

    if not user_id or not phone:
        return jsonify({"message": "بيانات غير مكتملة."}), HTTPStatus.BAD_REQUEST

    User = _get_user_model()
    # Check if phone is already taken
    existing = User.query.filter_by(phone_number=phone).first()
    if existing:
        return jsonify({"message": "رقم الجوال مسجل مسبقاً لمستخدم آخر."}), HTTPStatus.BAD_REQUEST

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "المستخدم غير موجود."}), HTTPStatus.NOT_FOUND

    user.phone_number = phone
    user.is_phone_verified = False
    db = _get_db()
    db.session.commit()

    sms_service = SMSService()
    sms_service.send_otp(phone, purpose='registration')

    return jsonify({"message": "تم ربط الرقم، يرجى التحقق."}), HTTPStatus.OK


@auth.post("/api/auth/login", endpoint="api_login")
@csrf.exempt
def api_login() -> tuple:
    """Authenticate a user and return a signed JWT token."""

    payload = _extract_json()
    identifier = (payload.get("identifier") or "").strip()
    password = payload.get("password")

    if not identifier or not password:
        return (
            jsonify({"error": "رقم الجوال/البريد وكلمة المرور مطلوبة."}),
            HTTPStatus.BAD_REQUEST,
        )

    User = _get_user_model()
    # Login by phone OR email
    user = User.query.filter(or_(User.phone_number == identifier, User.email == identifier)).first()
    
    if not user or not user.check_password(password):
        return (
            jsonify({"error": "بيانات الدخول غير صحيحة."}),
            HTTPStatus.UNAUTHORIZED,
        )

    if not user.is_active:
        return (
            jsonify({"error": "الحساب غير نشط. يرجى التواصل مع الدعم."}),
            HTTPStatus.FORBIDDEN,
        )

    normalized_role = user.normalized_role
    is_admin_account = normalized_role in {"admin", "superadmin"}

    # Legacy user handling: If logged in via email and phone not verified
    if not is_admin_account and (not user.phone_number or not user.is_phone_verified):
        # We allow session but marked as needing phone link
        # However, the requirement says "prompt for phone verify to continue"
        # Let's send a flag to the frontend to redirect to a phone linking page
        if not user.phone_number:
            return (
                jsonify(
                    {
                        "requires_phone": True,
                        "id": user.id,
                        "message": "يرجى تسجيل رقم الجوال للاستمرار.",
                    }
                ),
                HTTPStatus.OK,
            )
        # Phone exists but not verified
        return (
            jsonify(
                {
                    "requires_verification": True,
                    "phone": user.phone_number,
                    "message": "يرجى تأكيد رقم الجوال.",
                }
            ),
            HTTPStatus.OK,
        )

    token = create_token(user.id)
    # Establish the Flask-Login session
    from flask_login import logout_user
    logout_user()
    login_user(user)
    
    # ... (rest of the logic remains similar)
    role_source = current_user if current_user.is_authenticated else user
    member_role, company_role, admin_role, superadmin_role = user.ROLE_CHOICES
    
    member_dashboard_url = url_for("portal.member_portal_home")
    
    role_redirects = {
        member_role: member_dashboard_url,
        company_role: url_for("company_portal.company_usage_codes"),
        admin_role: url_for("admin.dashboard_alias"),
        superadmin_role: url_for("admin.dashboard_alias"),
    }
    normalized_role = getattr(role_source, "normalized_role", None) or role_source.role
    redirect_url = role_redirects.get(normalized_role, url_for("main.index"))
    
    response = jsonify({
        "token": token,
        "token_type": "Bearer",
        "role": user.role,
        "is_active": user.is_active,
        "redirect_url": redirect_url,
    })
    clear_auth_cookie(response)
    set_auth_cookie(response, token)
    return response, HTTPStatus.OK


@auth.get("/api/auth/profile", endpoint="profile")
def profile() -> tuple:
    """Return the authenticated user's profile details."""

    token = extract_bearer_token(request.headers.get("Authorization", ""))
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return (
            jsonify({"error": "Authentication token is required."}),
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


@auth.route("/forgot-password", methods=["GET"], endpoint="forgot_password")
def forgot_password() -> str:
    """Render the password reset request page for any account type."""

    return render_template("members/auth/forgot_password.html")


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
    """Send a password reset email or SMS containing a one-time token link."""

    data = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    identifier = (data.get("identifier") or "").strip().lower()
    
    if not identifier:
        return (
            jsonify({"message": "البريد الإلكتروني أو رقم الجوال مطلوب لإرسال رابط الاستعادة"}),
            HTTPStatus.BAD_REQUEST,
        )
    
    User = _get_user_model()
    # Find user by email or phone
    user = User.query.filter(or_(User.email == identifier, User.phone_number == identifier)).first()
    
    # Always return a generic response for security, unless it's a validation error
    success_msg = "إذا كان الحساب مسجلاً لدينا، ستصلك رسالة لإعادة تعيين كلمة المرور."
    
    if not user:
        return jsonify({"message": success_msg}), HTTPStatus.OK

    # Issue a password reset token
    token = generate_token(user.email or user.phone_number) # generate_token usually takes an identifier
    reset_url = f"{request.host_url}reset-password/{token}"
    
    # Determine delivery method
    if user.phone_number == identifier or (not user.email and user.phone_number):
        # Send via SMS
        sms_service = SMSService()
        message = f"رابط إعادة تعيين كلمة المرور لـ ELITE: {reset_url}"
        sms_service.send_sms(user.phone_number, message)
    else:
        # Send via Email
        send_email(
            user.email,
            "Reset Your Elite Discounts Password",
            "core/emails/password_reset.html",
            {"reset_url": reset_url, "recipient_name": user.username or user.email},
        )
        
    return jsonify({"message": success_msg}), HTTPStatus.OK


@auth.route("/reset-password/<token>", methods=["GET"], endpoint="reset_password_form")
def reset_password_form(token: str) -> str:
    """Render a browser-friendly password reset form for valid tokens.

    The UI is intentionally separated from the POST API to ensure that email links
    (opened via GET) lead to an informative page while preserving the API contract
    for programmatic password updates.
    """

    email = confirm_token(token)
    token_error = None

    if not email:
        token_error = "الرابط غير صالح أو منتهي الصلاحية. يرجى طلب رابط جديد لإعادة التعيين."
    else:
        User = _get_user_model()
        user = User.query.filter_by(email=email).first()
        if not user:
            token_error = "الرابط غير صالح أو منتهي الصلاحية. يرجى طلب رابط جديد لإعادة التعيين."

    if token_error:
        return render_template(
            "members/auth/reset_password.html",
            token_error=token_error,
            token=None,
        )

    return render_template(
        "members/auth/reset_password.html",
        token=token,
        token_error=None,
    )


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
    clear_auth_cookie(response)
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
