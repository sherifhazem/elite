"""Service helpers for partner usage codes and logging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets

from app.core.database import db
from app.models import ActivityLog, Offer, UsageCode
from app.modules.admin.services.admin_settings_service import get_admin_settings


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


def generate_usage_code(partner_id: int) -> UsageCode:
    """Create a fresh usage code for a partner, expiring any active code."""

    now = datetime.utcnow()
    settings = get_usage_code_settings()

    active_codes = (
        UsageCode.query.filter_by(partner_id=partner_id)
        .filter(UsageCode.expires_at > now)
        .all()
    )
    for active in active_codes:
        active.expires_at = now

    for _ in range(30):
        candidate = _generate_numeric_code()
        collision = (
            UsageCode.query.filter_by(code=candidate)
            .filter(UsageCode.expires_at > now)
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
    offer = Offer.query.get(offer_id)
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
        UsageCode.query.filter_by(partner_id=offer.company_id, code=normalized_code)
        .order_by(UsageCode.created_at.desc())
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

    if usage_code.usage_count >= usage_code.max_uses_per_window:
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
            "message": "Usage limit reached.",
        }

    usage_code.usage_count += 1
    log_usage_attempt(
        member_id=member_id,
        partner_id=partner_id,
        offer_id=offer_id,
        code_used=normalized_code,
        result="success",
    )
    return {
        "ok": True,
        "result": "success",
        "message": "Usage verified.",
        "usage_count": usage_code.usage_count,
        "max_uses_per_window": usage_code.max_uses_per_window,
        "expires_at": usage_code.expires_at.isoformat() if usage_code.expires_at else None,
    }


__all__ = [
    "UsageCodeSettings",
    "generate_usage_code",
    "get_usage_code_settings",
    "log_usage_attempt",
    "verify_usage_code",
]
