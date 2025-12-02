"""Company profile helpers kept outside model definitions."""

from __future__ import annotations

from typing import Dict

from app.core.database import db
from app.models import Company, User


def get_notification_preferences(company: Company) -> Dict[str, object]:
    """Return the company's notification preferences as a dictionary."""

    preferences = company.notification_preferences or {}
    if not isinstance(preferences, dict):
        return {}
    return preferences


def remove_company_owner_accounts(company: Company) -> None:
    """Delete owner accounts associated with the company without committing."""

    owner_ids = set()
    owners = []
    if company.owner is not None:
        owners.append(company.owner)

    owners.extend(
        User.query.filter(
            User.company_id == company.id,
            User.role == "company",
        ).all()
    )

    for owner in owners:
        if owner and owner.id not in owner_ids:
            owner_ids.add(owner.id)
            db.session.delete(owner)


__all__ = ["get_notification_preferences", "remove_company_owner_accounts"]
