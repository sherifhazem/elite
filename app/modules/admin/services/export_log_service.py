"""Service helpers for export activity logging."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import lazyload
from app.core.database import db
from app.models import ActivityLog

EXPORT_DEDUP_WINDOW_SECONDS = 30


def _has_recent_export(
    *,
    admin_id: int | None,
    action: str,
    filename: str,
    window_start: datetime,
) -> bool:
    query = (
        ActivityLog.query.options(
            lazyload(ActivityLog.admin),
            lazyload(ActivityLog.company),
            lazyload(ActivityLog.member),
            lazyload(ActivityLog.partner),
            lazyload(ActivityLog.offer),
        )
        .filter_by(admin_id=admin_id, action=action)
        .filter(ActivityLog.created_at >= window_start)
        .filter(ActivityLog.details.contains(filename))
        .with_for_update()
    )
    return query.first() is not None


def log_analytics_export(
    *,
    admin_id: int | None,
    date_from: datetime | None,
    date_to: datetime | None,
    filename: str,
) -> None:
    created_at = datetime.utcnow()
    with db.session.begin():
        if _has_recent_export(
            admin_id=admin_id,
            action="analytics_export",
            filename=filename,
            window_start=created_at - timedelta(seconds=EXPORT_DEDUP_WINDOW_SECONDS),
        ):
            return
        log_entry = ActivityLog(
            admin_id=admin_id,
            action="analytics_export",
            details=json.dumps(
                {
                    "admin_id": admin_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "filename": filename,
                }
            ),
            created_at=created_at,
            timestamp=created_at,
        )
        db.session.add(log_entry)


def log_reports_export(*, admin_id: int | None, filename: str) -> None:
    created_at = datetime.utcnow()
    with db.session.begin():
        if _has_recent_export(
            admin_id=admin_id,
            action="reports_export",
            filename=filename,
            window_start=created_at - timedelta(seconds=EXPORT_DEDUP_WINDOW_SECONDS),
        ):
            return
        log_entry = ActivityLog(
            admin_id=admin_id,
            action="reports_export",
            details=json.dumps(
                {
                    "admin_id": admin_id,
                    "filename": filename,
                }
            ),
            created_at=created_at,
            timestamp=created_at,
        )
        db.session.add(log_entry)


__all__ = ["log_analytics_export", "log_reports_export"]
