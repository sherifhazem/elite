"""Admin settings helpers backed by the database-backed lookup table."""

from __future__ import annotations

from typing import Dict, Iterable, List

from sqlalchemy.exc import IntegrityError

from app.logging.logger import get_logger
from app.core.choices.registry import CITIES, INDUSTRIES
from app.models import LookupChoice, db

_LOGGER = get_logger(__name__)
_VALID_TYPES = {"cities", "industries"}
_DEFAULTS = {"cities": CITIES, "industries": INDUSTRIES}


def _normalize_value(value: str) -> str:
    """Strip whitespace and coerce to a usable string."""

    return (value or "").strip()


def _ensure_storage_ready() -> None:
    """Create the lookup table if missing and seed defaults once."""

    LookupChoice.__table__.create(bind=db.engine, checkfirst=True)
    _seed_defaults()


def _seed_defaults() -> None:
    """Populate missing managed lists with the registry defaults."""

    for list_type, defaults in _DEFAULTS.items():
        existing = LookupChoice.query.filter_by(list_type=list_type).count()
        if existing:
            continue
        for value in defaults:
            normalized = _normalize_value(value)
            if not normalized:
                continue
            db.session.add(
                LookupChoice(list_type=list_type, name=normalized, active=True)
            )
    db.session.commit()


def _validate_type(list_type: str) -> str:
    normalized = (list_type or "").strip().lower()
    if normalized not in _VALID_TYPES:
        raise ValueError("قسم القائمة غير معروف.")
    return normalized


def get_all_settings(*, active_only: bool = True) -> Dict[str, List[str]]:
    """Return a copy of all managed settings."""

    return {
        "cities": get_list("cities", active_only=active_only),
        "industries": get_list("industries", active_only=active_only),
    }


def get_list(list_type: str, *, active_only: bool = True) -> List[str]:
    """Return a copy of the requested registry list."""

    _ensure_storage_ready()
    normalized = _validate_type(list_type)
    query = LookupChoice.query.filter_by(list_type=normalized)
    if active_only:
        query = query.filter_by(active=True)
    return [row.name for row in query.order_by(LookupChoice.name.asc()).all()]


def get_industry_items(*, active_only: bool = True) -> List[Dict[str, str | None]]:
    """Return industry items with icon metadata for admin use."""

    _ensure_storage_ready()
    query = LookupChoice.query.filter_by(list_type="industries")
    if active_only:
        query = query.filter_by(active=True)
    return [
        {"name": row.name, "icon": row.icon}
        for row in query.order_by(LookupChoice.name.asc()).all()
    ]


def update_settings(list_type: str, new_values: Iterable[str]) -> List[str]:
    """Replace the entire list while enforcing uniqueness and non-empty values."""

    _ensure_storage_ready()
    normalized = _validate_type(list_type)
    sanitized: list[str] = []
    seen = set()
    for raw in new_values:
        value = _normalize_value(str(raw))
        if not value or value in seen:
            continue
        sanitized.append(value)
        seen.add(value)

    LookupChoice.query.filter_by(list_type=normalized).delete()
    for value in sanitized:
        db.session.add(LookupChoice(list_type=normalized, name=value, active=True))
    db.session.commit()

    _LOGGER.info(
        "Admin settings list replaced", extra={"log_payload": {"list_type": normalized, "items": sanitized}}
    )
    return list(sanitized)


def add_item(list_type: str, name: str, *, is_active: bool | None = None) -> List[str]:
    """Append a new value to the registry list when valid."""

    _ensure_storage_ready()
    normalized_type = _validate_type(list_type)
    value = _normalize_value(name)
    is_active = True if is_active is None else bool(is_active)

    if not value:
        _LOGGER.warning("Admin settings change rejected", extra={"log_payload": {"admin_settings_action": f"add_{normalized_type}", "status": "error", "reason": "empty_value"}})
        raise ValueError("الاسم مطلوب.")

    entry = LookupChoice(list_type=normalized_type, name=value, active=is_active)
    db.session.add(entry)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        _LOGGER.warning(
            "Admin settings change rejected",
            extra={"log_payload": {"admin_settings_action": f"add_{normalized_type}", "status": "error", "reason": "duplicate_value"}},
        )
        raise ValueError("العنصر موجود بالفعل.")

    _LOGGER.info(
        "Admin settings change applied",
        extra={
            "log_payload": {
                "admin_settings_action": f"add_{normalized_type}",
                "status": "success",
                "value": value,
                "items": get_list(normalized_type, active_only=False),
            }
        },
    )
    return get_list(normalized_type, active_only=True)


def delete_item(list_type: str, name: str) -> List[str]:
    """Remove a value from the registry list when present."""

    _ensure_storage_ready()
    normalized_type = _validate_type(list_type)
    value = _normalize_value(name)
    if not value:
        raise ValueError("قيمة غير صالحة للحذف.")

    deleted = (
        LookupChoice.query.filter_by(list_type=normalized_type, name=value)
        .delete()
    )
    if not deleted:
        raise ValueError("لم يتم العثور على العنصر المطلوب.")
    db.session.commit()

    _LOGGER.info(
        "Admin settings change applied",
        extra={
            "log_payload": {
                "admin_settings_action": f"delete_{normalized_type}",
                "status": "success",
                "value": value,
                "items": get_list(normalized_type, active_only=False),
            }
        },
    )
    return get_list(normalized_type, active_only=True)


def get_section(section: str, *, active_only: bool = True):
    """Return a settings section for the supported registries."""

    normalized = (section or "").strip().lower()
    if normalized == "membership_discounts":
        _LOGGER.info(
            "Deprecated membership discounts requested", extra={"log_payload": {"list_type": normalized}}
        )
        return []
    return get_list(normalized, active_only=active_only)


def save_list(section: str, new_values: Iterable):
    """Persist the given settings section, routing to the proper handler."""

    normalized = (section or "").strip().lower()
    if normalized == "membership_discounts":
        _LOGGER.info(
            "Ignoring deprecated membership discounts payload",
            extra={"log_payload": {"list_type": normalized, "items": list(new_values)}},
        )
        return []
    return update_settings(normalized, new_values)


def update_item(
    list_type: str,
    old_name: str,
    new_name: str,
    *,
    is_active: bool | None = None,
) -> List[str]:
    """Rename an existing entry while preventing duplicates."""

    _ensure_storage_ready()
    normalized_type = _validate_type(list_type)
    new_value = _normalize_value(new_name)
    old_value = _normalize_value(old_name)

    if not new_value:
        raise ValueError("الاسم مطلوب.")

    entry = LookupChoice.query.filter_by(list_type=normalized_type, name=old_value).first()
    if not entry:
        raise ValueError("لم يتم العثور على العنصر المطلوب.")

    if new_value != old_value:
        duplicate = LookupChoice.query.filter_by(list_type=normalized_type, name=new_value).first()
        if duplicate:
            raise ValueError("العنصر موجود بالفعل.")
        entry.name = new_value

    if is_active is not None:
        entry.active = bool(is_active)

    db.session.commit()
    _LOGGER.info(
        "Admin settings change applied",
        extra={
            "log_payload": {
                "admin_settings_action": f"update_{normalized_type}",
                "status": "success",
                "value": new_value,
                "items": get_list(normalized_type, active_only=False),
            }
        },
    )
    return get_list(normalized_type, active_only=True)


def update_industry_icon(name: str, icon: str | None) -> List[Dict[str, str | None]]:
    """Set or clear the icon for a specific industry."""

    _ensure_storage_ready()
    value = _normalize_value(name)
    if not value:
        raise ValueError("العنصر المطلوب مفقود.")

    entry = LookupChoice.query.filter_by(list_type="industries", name=value).first()
    if not entry:
        raise ValueError("لم يتم العثور على العنصر المطلوب.")

    entry.icon = icon or None
    db.session.commit()

    _LOGGER.info(
        "Admin settings change applied",
        extra={
            "log_payload": {
                "admin_settings_action": "update_industry_icon",
                "status": "success",
                "value": value,
                "icon": entry.icon,
            }
        },
    )
    return get_industry_items(active_only=False)


__all__ = [
    "get_all_settings",
    "get_list",
    "get_section",
    "save_list",
    "update_settings",
    "add_item",
    "delete_item",
    "update_item",
    "get_industry_items",
    "update_industry_icon",
]
