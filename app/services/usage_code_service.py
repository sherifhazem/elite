"""Service helpers for partner usage codes and logging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets

from app.core.database import db
from sqlalchemy.orm import lazyload
from app.models import ActivityLog, Offer, UsageCode
from app.modules.admin.services.admin_settings_service import get_admin_settings
from app.services.incentive_eligibility_service import evaluate_offer_eligibility


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
    max_uses_per_window = int(
        verification.get("usage_code_max_uses_per_window")
        or verification.get("max_uses_per_minute")
        or 5
    )
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


def generate_usage_code(partner_id: int) -> UsageCode:
    """Create a fresh usage code for a partner, expiring any active code."""

    now = datetime.utcnow()
    settings = get_usage_code_settings()

    _usage_code_query().filter(UsageCode.expires_at > now).with_for_update().all()
    active_codes = (
        _usage_code_query()
        .filter_by(partner_id=partner_id)
        .filter(UsageCode.expires_at > now)
        .with_for_update()
        .all()
    )
    for active in active_codes:
        active.expires_at = now

    code_value = None
    for _ in range(30):
        candidate = _generate_numeric_code()
        collision = (
            _usage_code_query()
            .filter_by(code=candidate)
            .filter(UsageCode.expires_at > now)
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
    db.session.commit()
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
    """Validate a usage code for a selected offer and record the attempt."""

    normalized_code = (code or "").strip()
    session = db.session
    is_in_txn = False
    if hasattr(session, "in_transaction"):
        is_in_txn = session.in_transaction()
    elif hasattr(session, "get_transaction"):
        is_in_txn = session.get_transaction() is not None
    else:
        is_in_txn = session.is_active

    transaction_context = (
        session.begin_nested() if is_in_txn else session.begin()
    )
    with transaction_context:
        offer = Offer.query.filter_by(id=offer_id).with_for_update().first()
        partner_id = offer.company_id if offer else None

        if not normalized_code.isdigit() or len(normalized_code) not in (4, 5):
            log_usage_attempt(
                member_id=member_id,
                partner_id=partner_id,
                offer_id=offer_id,
                code_used=normalized_code,
                result="invalid",
            )
            return {"ok": False, "result": "invalid", "message": "Invalid code format."}

        if offer is None or offer.company_id is None:
            log_usage_attempt(
                member_id=member_id,
                partner_id=partner_id,
                offer_id=offer_id,
                code_used=normalized_code,
                result="invalid",
            )
            return {"ok": False, "result": "invalid", "message": "Offer not found."}

        usage_code = (
            _usage_code_query()
            .filter_by(partner_id=offer.company_id, code=normalized_code)
            .order_by(UsageCode.created_at.desc())
            .with_for_update()
            .first()
        )
        if usage_code is None:
            log_usage_attempt(
                member_id=member_id,
                partner_id=partner_id,
                offer_id=offer_id,
                code_used=normalized_code,
                result="invalid",
            )
            return {"ok": False, "result": "invalid", "message": "Code is invalid."}

        if usage_code.is_expired():
            log_usage_attempt(
                member_id=member_id,
                partner_id=partner_id,
                offer_id=offer_id,
                code_used=normalized_code,
                result="expired",
            )
            return {"ok": False, "result": "expired", "message": "Code has expired."}

        eligibility = evaluate_offer_eligibility(member_id, offer_id)
        if not eligibility["eligible"]:
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
                "reason": eligibility["reason"],
            }

        window_start = usage_code.created_at
        window_end = usage_code.expires_at
        successful_attempts = (
            ActivityLog.query.filter_by(
                action="usage_code_attempt",
                partner_id=partner_id,
                code_used=normalized_code,
            )
            .filter(ActivityLog.result.in_(["valid", "success"]))
            .filter(ActivityLog.created_at >= window_start)
            .with_for_update()
        )
        if window_end:
            successful_attempts = successful_attempts.filter(
                ActivityLog.created_at <= window_end
            )

        if member_id is not None:
            prior_attempt = successful_attempts.filter(
                member_id=member_id, offer_id=offer_id
            )
            if prior_attempt.first() is not None:
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
                    "message": "Usage already verified for this offer.",
                }

        if successful_attempts.count() >= usage_code.max_uses_per_window:
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
                "message": "Usage limit reached.",
            }

        usage_code.usage_count += 1
        log_usage_attempt(
            member_id=member_id,
            partner_id=partner_id,
            offer_id=offer_id,
            code_used=normalized_code,
            result="valid",
        )
        return {
            "ok": True,
            "result": "valid",
            "message": "Usage verified.",
            "usage_count": usage_code.usage_count,
            "max_uses_per_window": usage_code.max_uses_per_window,
            "expires_at": usage_code.expires_at.isoformat()
            if usage_code.expires_at
            else None,
        }


__all__ = [
    "UsageCodeSettings",
    "generate_usage_code",
    "get_usage_code_settings",
    "log_usage_attempt",
    "verify_usage_code",
]
