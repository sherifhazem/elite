"""Admin-configurable settings backed by the centralized key-value store."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from app.logging.logger import get_logger
from app.models import AdminSetting, db

_LOGGER = get_logger(__name__)

_ALLOWED_CODE_FORMATS = {"5_digits", "1_letter_4_digits"}
_ALLOWED_GRACE_MODES = {"end_of_next_week"}


def _default_member_activity_rules() -> dict:
    return {
        "required_usages": 1,
        "time_window_days": 7,
        "active_grace_mode": "end_of_next_week",
    }


def _default_partner_activity_rules() -> dict:
    return {
        "required_usages": 1,
        "require_unique_customers": False,
        "time_window_days": 7,
        "active_grace_mode": "end_of_next_week",
    }


def _default_verification_settings() -> dict:
    return {
        "code_format": "5_digits",
        "code_expiry_seconds": 60,
        "max_uses_per_minute": 3,
        "usage_code_expiry_seconds": 300,
        "usage_code_max_uses_per_window": 5,
    }


def _default_offer_types() -> dict:
    return {
        "first_time_offer": False,
        "loyalty_offer": False,
        "active_members_only": False,
        "happy_hour": False,
        "mid_week": False,
    }


def _coerce_int(value: Any, field: str, *, minimum: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{field} يجب أن يكون رقماً صحيحاً.") from exc
    if minimum is not None and number < minimum:
        raise ValueError(f"{field} يجب ألا يكون أقل من {minimum}.")
    return number


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"true", "1", "yes", "y", "on"}
    return bool(value)


def _coerce_code_format(value: Any) -> str:
    normalized = (str(value or "").strip() or "5_digits")
    if normalized not in _ALLOWED_CODE_FORMATS:
        raise ValueError("صيغة رمز التحقق غير صالحة.")
    return normalized


def _coerce_grace_mode(value: Any) -> str:
    normalized = str(value or "").strip() or "end_of_next_week"
    if normalized not in _ALLOWED_GRACE_MODES:
        raise ValueError("سياسة انتهاء النشاط غير صالحة.")
    return normalized


def _merge(defaults: Mapping[str, Any], stored: Mapping[str, Any] | None) -> Dict[str, Any]:
    merged = dict(defaults)
    if not stored:
        return merged
    for key, value in stored.items():
        if key in merged:
            merged[key] = value
    return merged


def _load_setting(key: str, defaults: Mapping[str, Any]) -> Dict[str, Any]:
    record = AdminSetting.query.filter_by(key=key).first()
    stored_value = record.value if record and isinstance(record.value, dict) else {}

    # backward compatibility for prior offer key
    if key == "offer_types" and "loyalty_offerOffer" in stored_value:
        stored_value = dict(stored_value)
        stored_value.setdefault("loyalty_offer", stored_value.get("loyalty_offerOffer"))

    merged = _merge(defaults, stored_value)
    return merged


def get_admin_settings() -> Dict[str, Dict[str, Any]]:
    """Return admin-managed configuration merged with defaults."""

    return {
        "member_activity_rules": _load_setting(
            "member_activity_rules", _default_member_activity_rules()
        ),
        "partner_activity_rules": _load_setting(
            "partner_activity_rules", _default_partner_activity_rules()
        ),
        "verification_code": _load_setting(
            "verification_code", _default_verification_settings()
        ),
        "offer_types": _load_setting("offer_types", _default_offer_types()),
    }


def _persist_setting(key: str, payload: Mapping[str, Any]) -> None:
    record = AdminSetting.query.filter_by(key=key).first()
    if record:
        record.value = dict(payload)
    else:
        record = AdminSetting(key=key, value=dict(payload))
        db.session.add(record)


def save_admin_settings(payload: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Validate and persist admin-configurable settings."""

    member_activity = _default_member_activity_rules()
    partner_activity = _default_partner_activity_rules()
    verification_settings = _default_verification_settings()
    offer_types = _default_offer_types()

    member_activity.update(
        {
            "required_usages": _coerce_int(
                payload.get("member_required_usages", member_activity["required_usages"]),
                "عدد الاستخدامات المطلوبة للأعضاء",
                minimum=0,
            ),
            "time_window_days": _coerce_int(
                payload.get("member_time_window_days", member_activity["time_window_days"]),
                "فترة التتبع (أيام) للأعضاء",
                minimum=1,
            ),
            "active_grace_mode": _coerce_grace_mode(
                payload.get("member_active_grace_mode"),
            ),
        }
    )

    partner_activity.update(
        {
            "required_usages": _coerce_int(
                payload.get("partner_required_usages", partner_activity["required_usages"]),
                "عدد الاستخدامات المطلوبة للشركاء",
                minimum=0,
            ),
            "require_unique_customers": _coerce_bool(
                payload.get(
                    "partner_require_unique_customers",
                    partner_activity["require_unique_customers"],
                )
            ),
            "time_window_days": _coerce_int(
                payload.get(
                    "partner_time_window_days", partner_activity["time_window_days"]
                ),
                "فترة التتبع (أيام) للشركاء",
                minimum=1,
            ),
            "active_grace_mode": _coerce_grace_mode(
                payload.get("partner_active_grace_mode"),
            ),
        }
    )

    verification_settings.update(
        {
            "code_format": _coerce_code_format(
                payload.get("code_format", verification_settings["code_format"])
            ),
            "code_expiry_seconds": _coerce_int(
                payload.get(
                    "code_expiry_seconds", verification_settings["code_expiry_seconds"]
                ),
                "مدة صلاحية رمز التحقق (ثواني)",
                minimum=1,
            ),
            "max_uses_per_minute": _coerce_int(
                payload.get(
                    "max_uses_per_minute",
                    verification_settings["max_uses_per_minute"],
                ),
                "الحد الأقصى للاستخدام في الدقيقة",
                minimum=1,
            ),
            "usage_code_expiry_seconds": _coerce_int(
                payload.get(
                    "usage_code_expiry_seconds",
                    verification_settings["usage_code_expiry_seconds"],
                ),
                "مدة صلاحية رمز الاستخدام (ثواني)",
                minimum=1,
            ),
            "usage_code_max_uses_per_window": _coerce_int(
                payload.get(
                    "usage_code_max_uses_per_window",
                    verification_settings["usage_code_max_uses_per_window"],
                ),
                "الحد الأقصى لاستخدام رمز الاستخدام",
                minimum=1,
            ),
        }
    )

    offer_types.update(
        {
            "first_time_offer": _coerce_bool(payload.get("first_time_offer")),
            "loyalty_offer": _coerce_bool(
                payload.get("loyalty_offer", payload.get("loyalty_offerOffer"))
            ),
            "active_members_only": _coerce_bool(payload.get("active_members_only")),
            "happy_hour": _coerce_bool(payload.get("happy_hour")),
            "mid_week": _coerce_bool(payload.get("mid_week")),
        }
    )

    _persist_setting("member_activity_rules", member_activity)
    _persist_setting("partner_activity_rules", partner_activity)
    _persist_setting("verification_code", verification_settings)
    _persist_setting("offer_types", offer_types)

    db.session.commit()

    _LOGGER.info(
        "Admin settings updated",
        extra={
            "log_payload": {
                "member_activity_rules": member_activity,
                "partner_activity_rules": partner_activity,
                "verification_code": verification_settings,
                "offer_types": offer_types,
            }
        },
    )

    return get_admin_settings()


__all__ = ["get_admin_settings", "save_admin_settings"]
