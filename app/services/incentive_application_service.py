"""Apply incentives after successful usage verification."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from app.core.database import db
from app.models import ActivityLog, Offer
from app.modules.admin.services.admin_settings_service import get_admin_settings
from app.services.incentive_eligibility_service import evaluate_offer_eligibility


def _end_of_next_week(now: datetime) -> datetime:
    end_of_week_date = now.date() + timedelta(days=(6 - now.weekday()))
    end_of_week = datetime.combine(end_of_week_date, time(23, 59, 59))
    return end_of_week + timedelta(days=7)


def _resolve_incentive_type(offer: Offer, settings: dict) -> str | None:
    classifications = set(offer.classification_values)
    offer_types = settings.get("offer_types", {})

    if "first_time_offer" in classifications and bool(
        offer_types.get("first_time_offer", False)
    ):
        return "first_time"
    if "loyalty_offer" in classifications and bool(
        offer_types.get("loyalty_offer", False)
    ):
        return "loyalty"
    return None


def _resolve_grace_valid_until(settings: dict, now: datetime) -> datetime | None:
    rules = settings.get("member_activity_rules", {})
    mode = rules.get("active_grace_mode")
    if mode == "end_of_next_week":
        return _end_of_next_week(now)
    return None


def _resolve_incentive_window(
    settings: dict, now: datetime
) -> tuple[datetime | None, datetime | None]:
    valid_until = _resolve_grace_valid_until(settings, now)
    if valid_until is None:
        return None, None
    week_start_date = now.date() - timedelta(days=now.weekday())
    window_start = datetime.combine(week_start_date, time.min)
    return window_start, valid_until


def _has_recent_incentive(
    *,
    member_id: int | None,
    offer_id: int,
    incentive_result: str,
    window_start: datetime | None,
    window_end: datetime | None,
    for_update: bool = False,
) -> bool:
    query = ActivityLog.query.filter_by(
        action="incentive_applied",
        member_id=member_id,
        offer_id=offer_id,
        result=incentive_result,
    )
    if for_update:
        query = query.with_for_update()
    if window_start is not None:
        query = query.filter(ActivityLog.created_at >= window_start)
    if window_end is not None:
        query = query.filter(ActivityLog.created_at <= window_end)
    return query.first() is not None


def apply_incentive(
    member_id: int | None, offer_id: int, usage_result: dict
) -> dict:
    """Apply incentive for a verified usage and record the activity log."""

    now = datetime.utcnow()
    applied = False
    incentive_type: str | None = None
    valid_until: datetime | None = None

    eligibility = evaluate_offer_eligibility(member_id, offer_id)
    offer = Offer.query.get(offer_id)

    if (
        usage_result.get("ok")
        and usage_result.get("result") == "valid"
        and eligibility.get("eligible")
        and offer is not None
    ):
        settings = get_admin_settings()
        incentive_type = _resolve_incentive_type(offer, settings)
        if incentive_type not in {"first_time", "loyalty"}:
            incentive_type = None
        if incentive_type:
            valid_until = _resolve_grace_valid_until(settings, now)
            window_start, window_end = _resolve_incentive_window(settings, now)
            with db.session.begin():
                if _has_recent_incentive(
                    member_id=member_id,
                    offer_id=offer_id,
                    incentive_result=incentive_type,
                    window_start=window_start,
                    window_end=window_end,
                    for_update=True,
                ):
                    return {
                        "applied": False,
                        "incentive_type": incentive_type,
                        "valid_until": valid_until.isoformat() if valid_until else None,
                    }

                log_entry = ActivityLog(
                    admin_id=None,
                    company_id=None,
                    action="incentive_applied",
                    details=f"Incentive applied result: {incentive_type}",
                    member_id=member_id,
                    partner_id=offer.company_id if offer else None,
                    offer_id=offer_id,
                    code_used=None,
                    result=incentive_type,
                    created_at=now,
                    timestamp=now,
                )
                db.session.add(log_entry)
                applied = True

    return {
        "applied": applied,
        "incentive_type": incentive_type,
        "valid_until": valid_until.isoformat() if valid_until else None,
    }


__all__ = ["apply_incentive"]
