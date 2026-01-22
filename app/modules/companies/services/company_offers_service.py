# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Service helpers for offer presentation across member and company portals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import joinedload

from app.models import Company, Offer, LookupChoice


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


def get_portal_offers_with_company(limit: Optional[int] = None, featured: bool = False) -> List[OfferCompanyBundle]:
    """Return offer records enriched with linked company data for the portal."""
    # Pre-fetch industry icons to avoid multiple DB queries
    industry_icons = {
        row.name: row.icon 
        for row in LookupChoice.query.filter_by(list_type="industries").all()
    }

    query = Offer.query.options(joinedload(Offer.company)).filter(Offer.status == "active")
    
    if featured:
        query = query.order_by(Offer.created_at.desc())
    else:
        query = query.order_by(Offer.valid_until.asc())

    if limit:
        query = query.limit(limit)

    offers: Iterable[Offer] = query.all()

    results: List[OfferCompanyBundle] = []
    for offer in offers:
        company = offer.company
        industry_name = company.industry if company else None
        industry_icon = industry_icons.get(industry_name) if industry_name else None
        
        bundle = OfferCompanyBundle(
            id=offer.id,
            title=offer.title,
            description=offer.description,
            base_discount=float(offer.base_discount or 0.0),
            valid_until=offer.valid_until,
            membership_discount=float(offer.base_discount or 0.0),
            company={
                "id": company.id if company else "",
                "name": company.name if company else "شريك ELITE",
                "summary": _summarize_company(company),
                "description": (company.description or "") if company else "",
                "logo_url": company.logo_url if company else None,
                "industry": industry_name,
                "industry_icon": industry_icon,
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
        "logo_url": company.logo_url,
        "industry": company.industry,
    }


def list_company_offers(company_id: int) -> List[Offer]:
    """Return company-scoped offers ordered alphabetically for filters."""

    return (
        Offer.query.filter_by(company_id=company_id)
        .filter(Offer.status == "active")
        .order_by(Offer.title.asc())
        .all()
    )


__all__ = [
    "OfferCompanyBundle",
    "get_portal_offers_with_company",
    "get_company_brief",
    "list_company_offers",
]

