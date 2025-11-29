# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Service helpers for offer presentation across member and company portals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import joinedload

from app.models import Company, Offer
<<<<<<< HEAD
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)

service_logger = get_service_logger(__name__)


def _log(function: str, event: str, message: str, details: Dict[str, object] | None = None, level: str = "INFO") -> None:
    """Emit standardized observability events for offer services."""

    normalized_level = level.upper()
    if normalized_level == "ERROR" or event in {"soft_failure", "validation_failure"}:
        log_service_error(__name__, function, message, details=details, event=event)
    elif event == "service_start":
        log_service_start(__name__, function, message, details)
    elif event in {"service_complete", "service_success"}:
        log_service_success(__name__, function, message, details=details, event=event)
    else:
        log_service_step(__name__, function, message, details=details, event=event, level=level)
=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))


@dataclass
class OfferCompanyBundle:
    """Lightweight container exposing offer and company metadata for templates."""

    id: int
    title: str
    description: str | None
    base_discount: float
    valid_until: Optional[object]
    membership_discount: float
    company: Dict[str, object]


def _summarize_company(company: Optional[Company], *, length: int = 140) -> str:
    """Return a compact summary of the company's description."""

    if company is None:
        return ""
    description = (company.description or "").strip()
    if not description:
        return ""
    if len(description) <= length:
        return description
    return f"{description[:length].rstrip()}…"


def get_portal_offers_with_company(
    membership_level: str | None = None,
) -> List[OfferCompanyBundle]:
    """Return offer records enriched with linked company data for the portal."""

    normalized_level = (membership_level or "Basic").strip().title() or "Basic"
    offers: Iterable[Offer] = (
        Offer.query.options(joinedload(Offer.company))
        .order_by(Offer.valid_until.asc())
        .all()
    )

    results: List[OfferCompanyBundle] = []
    for offer in offers:
        company = offer.company
        bundle = OfferCompanyBundle(
            id=offer.id,
            title=offer.title,
            description=offer.description,
            base_discount=float(offer.base_discount or 0.0),
            valid_until=offer.valid_until,
            membership_discount=float(offer.get_discount_for_level(normalized_level)),
            company={
                "id": company.id if company else "",
                "name": company.name if company else "شريك ELITE",
                "summary": _summarize_company(company),
                "description": (company.description or "") if company else "",
            },
        )
        results.append(bundle)
    return results


def get_company_brief(company_id: int) -> Optional[Dict[str, object]]:
    """Return a read-only snapshot of the company information for the portal."""

    company = Company.query.get(company_id)
    if company is None:
        return None
    return {
        "id": company.id,
        "name": company.name,
        "description": company.description or "",
        "summary": _summarize_company(company, length=220),
    }


def list_company_offers(company_id: int) -> List[Offer]:
    """Return company-scoped offers ordered alphabetically for filters."""

    return (
        Offer.query.filter_by(company_id=company_id)
        .order_by(Offer.title.asc())
        .all()
    )


__all__ = [
    "OfferCompanyBundle",
    "get_portal_offers_with_company",
    "get_company_brief",
    "list_company_offers",
]

