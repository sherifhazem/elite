"""Service helpers for partner usage codes and logging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets

from app.core.database import db
from flask import current_app
from sqlalchemy import or_
from sqlalchemy.orm import lazyload
from app.models import ActivityLog, Offer, UsageCode
from app.modules.admin.services.admin_settings_service import get_admin_settings
from app.services.incentive_eligibility_service import evaluate_offer_eligibility


USAGE_CODE_MAX_USES = 10


@dataclass(frozen=True)
class UsageCodeSettings:
    expiry_seconds: int
    max_uses_per_window: int


def get_usage_code_settings() -> UsageCodeSettings:
    """Return usage-code settings sourced from admin configuration."""

    verification = get_admin_settings().get("verification_code", {})
    expiry_seconds = int(
        verification.get("usage_code_expiry_seconds")
        or verification.get("code_expiry_seconds")
        or 300
    )
    max_uses_per_window = USAGE_CODE_MAX_USES
    return UsageCodeSettings(
        expiry_seconds=max(expiry_seconds, 1),
        max_uses_per_window=max(max_uses_per_window, 1),
    )


def _generate_numeric_code() -> str:
    """Generate a 4-5 digit numeric code as a string."""

    length = 4 if secrets.randbelow(2) == 0 else 5
    minimum = 10 ** (length - 1)
    maximum = (10**length) - 1
    return str(secrets.randbelow(maximum - minimum + 1) + minimum)


def _usage_code_query():
    """Return a usage code query without eager-loading partner relationships."""

    return UsageCode.query.options(lazyload(UsageCode.partner))


def _active_usage_code_filter(query, now: datetime):
    """Restrict a usage code query to active (non-expired) codes."""

    return query.filter(
        or_(UsageCode.expires_at.is_(None), UsageCode.expires_at > now)
    )


def generate_usage_code(partner_id: int, *, commit: bool = True) -> UsageCode:
    """Create a fresh usage code for a partner, expiring any active code."""

    now = datetime.utcnow()
    settings = get_usage_code_settings()

    _active_usage_code_filter(_usage_code_query(), now).with_for_update().all()
    active_codes = (
        _active_usage_code_filter(
            _usage_code_query().filter_by(partner_id=partner_id),
            now,
        )
        .with_for_update()
        .all()
    )
    for active in active_codes:
        active.expires_at = now

    code_value = None
    for _ in range(30):
        candidate = _generate_numeric_code()
        collision = (
            _active_usage_code_filter(
                _usage_code_query().filter_by(code=candidate),
                now,
            )
            .with_for_update()
            .first()
        )
        if collision is None:
            code_value = candidate
            break
    else:  # pragma: no cover - extreme collision edge case
        raise RuntimeError("Unable to generate a unique usage code.")

    usage_code = UsageCode(
        code=code_value,
        partner_id=partner_id,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.expiry_seconds),
        usage_count=0,
        max_uses_per_window=settings.max_uses_per_window,
    )
    db.session.add(usage_code)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return usage_code


def log_usage_attempt(
    *,
    member_id: int | None,
    partner_id: int | None,
    offer_id: int | None,
    code_used: str | None,
    result: str,
) -> ActivityLog:
    """Persist a usage verification attempt in the activity log."""

    created_at = datetime.utcnow()
    entry = ActivityLog(
        admin_id=None,
        company_id=None,
        action="usage_code_attempt",
        details=f"Usage code attempt result: {result}",
        member_id=member_id,
        partner_id=partner_id,
        offer_id=offer_id,
        code_used=code_used,
        result=result,
        created_at=created_at,
        timestamp=created_at,
    )
    db.session.add(entry)
    return entry


def verify_usage_code(
        *,
        member_id: int | None,
        offer_id: int,
        code: str,
) -> dict:
    """
    التحقق من كود الاستخدام لعرض محدد وتسجيل المحاولة في سجل النشاطات.
    تم تحديث الدالة لضمان التوافق مع PostgreSQL وإدارة المعاملات بشكل آمن.
    """

    normalized_code = (code or "").strip()
    session = db.session

    # 1. تحديد حالة المعاملة (Transaction) لضمان الحفظ الصحيح
    is_in_txn = False
    if hasattr(session, "in_transaction"):
        is_in_txn = session.in_transaction()
    elif hasattr(session, "get_transaction"):
        is_in_txn = session.get_transaction() is not None
    else:
        is_in_txn = session.is_active

    # استخدام معاملة متداخلة (Nested) إذا كنا داخل معاملة بالفعل، أو معاملة جديدة
    transaction_context = session.begin_nested() if is_in_txn else session.begin()

    try:
        with transaction_context:
            # 2. جلب بيانات العرض (بدون قفل لتجنب مشاكل الـ Join في Postgres)
            offer = Offer.query.filter_by(id=offer_id).first()
            partner_id = offer.company_id if offer else None

            # 3. التحقق من صيغة الكود
            if not normalized_code.isdigit() or len(normalized_code) not in (4, 5):
                log_usage_attempt(
                    member_id=member_id,
                    partner_id=partner_id,
                    offer_id=offer_id,
                    code_used=normalized_code,
                    result="invalid",
                )
                return {"ok": False, "result": "invalid", "message": "صيغة الكود غير صحيحة."}

            if offer is None:
                return {"ok": False, "result": "not_found", "message": "العرض غير موجود."}

            # 4. جلب كود التفعيل الخاص بالشريك (استخدام filter_by بدقة)
            usage_code = (
                UsageCode.query.filter_by(
                    partner_id=offer.company_id,
                    code=normalized_code,
                )
                .with_for_update()
                .first()
            )

            if not usage_code:
                log_usage_attempt(
                    member_id=member_id,
                    partner_id=partner_id,
                    offer_id=offer_id,
                    code_used=normalized_code,
                    result="not_found",
                )
                return {"ok": False, "result": "not_found", "message": "كود التفعيل غير صحيح."}

            if usage_code.is_expired():
                log_usage_attempt(
                    member_id=member_id,
                    partner_id=partner_id,
                    offer_id=offer_id,
                    code_used=normalized_code,
                    result="expired",
                )
                return {"ok": False, "result": "expired", "message": "انتهت صلاحية الكود."}

            # 5. التحقق من أهلية العضو (Eligibility)
            eligibility = evaluate_offer_eligibility(member_id, offer_id)
            if not eligibility["eligible"]:
                reason_code = eligibility.get("reason", "unknown")
                
                # Eligibility failure messages (Arabic)
                messages = {
                    "already_claimed": "عذراً، هذا العرض مخصص للاستخدام مرة واحدة فقط.",
                    "loyalty_requirement_not_met": "عذراً، هذا العرض مخصص لعملاء الولاء (يتطلب استخدامين سابقين).",
                    "inactive_member": "عذراً، هذا العرض مخصص للأعضاء النشطين فقط.",
                    "disabled_offer": "هذا العرض غير متاح حالياً.",
                    "inactive_partner": "الشريك غير نشط حالياً."
                }
                
                log_usage_attempt(
                    member_id=member_id,
                    partner_id=partner_id,
                    offer_id=offer_id,
                    code_used=normalized_code,
                    result="not_eligible",
                )
                return {
                    "ok": False,
                    "result": "not_eligible",
                    "message": messages.get(reason_code, "أنت غير مؤهل لهذا العرض.")
                }

            # 6. التحقق من حدود الاستخدام
            window_start = usage_code.created_at
            window_end = usage_code.expires_at

            successful_attempts_query = ActivityLog.query.filter_by(
                action="usage_code_attempt",
                partner_id=partner_id,
                code_used=normalized_code,
            ).filter(
                ActivityLog.result.in_(["valid", "success"]),
                ActivityLog.created_at >= window_start
            )

            if window_end:
                successful_attempts_query = successful_attempts_query.filter(
                    ActivityLog.created_at <= window_end
                )

            # التحقق من تكرار الاستخدام لنفس العضو
            if member_id is not None:
                prior_attempt = successful_attempts_query.filter_by(
                    member_id=member_id,
                    offer_id=offer_id
                ).first()

                if prior_attempt is not None:
                    log_usage_attempt(
                        member_id=member_id,
                        partner_id=partner_id,
                        offer_id=offer_id,
                        code_used=normalized_code,
                        result="usage_limit_reached",
                    )
                    return {
                        "ok": False,
                        "result": "usage_limit_reached",
                        "message": "تم تفعيل هذا العرض مسبقاً لهذا العضو."
                    }

            # 7. التحقق من الحد الأقصى للاستخدام في النافذة الزمنية
            if usage_code.usage_count >= usage_code.max_uses_per_window:
                generate_usage_code(partner_id, commit=False)
                log_usage_attempt(
                    member_id=member_id,
                    partner_id=partner_id,
                    offer_id=offer_id,
                    code_used=normalized_code,
                    result="limit_exceeded",
                )
                return {
                    "ok": False,
                    "result": "limit_exceeded",
                    "message": "تم تحديث الكود بعد استهلاك الحد الأقصى.",
                }

            # 8. النجاح: تسجيل النشاط النهائي
            log_usage_attempt(
                member_id=member_id,
                partner_id=partner_id,
                offer_id=offer_id,
                code_used=normalized_code,
                result="valid",
            )
            usage_code.usage_count += 1

            # تأكيد الحفظ في قاعدة البيانات قبل الخروج من سياق المعاملة
            session.flush()

            # 9. التزام الحفظ النهائي (Commit)
        if not is_in_txn:
            session.commit()

        if usage_code.usage_count >= usage_code.max_uses_per_window:
            generate_usage_code(partner_id, commit=False)

        return {
            "ok": True,
            "result": "valid",
            "message": "تم تفعيل العرض بنجاح.",
            "usage_count": usage_code.usage_count,
            "max_uses": usage_code.max_uses_per_window,
            "expires_at": window_end.isoformat() if window_end else None
        }

    except Exception as e:
        session.rollback()
        # تسجيل الخطأ في الـ Logs للنظام
        current_app.logger.error(f"Error in verify_usage_code: {str(e)}")
        return {"ok": False, "result": "error", "message": "حدث خطأ أثناء معالجة الطلب."}


__all__ = [
    "UsageCodeSettings",
    "generate_usage_code",
    "get_usage_code_settings",
    "log_usage_attempt",
    "verify_usage_code",
]
