"""Business logic for managing companies from the admin panel."""

from __future__ import annotations

from typing import Dict

from app.core.database import db
from app.models import Company
from app.services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_reactivation_email,
    send_company_suspension_email,
)


def fetch_companies_by_status(status: str) -> tuple[list[Company], Dict[str, int]]:
    """Return companies for the requested status alongside status counts."""

    normalized = (status or "pending").lower()
    companies = Company.query.filter_by(status=normalized).all()
    status_counts = {
        "pending": Company.query.filter_by(status="pending").count(),
        "approved": Company.query.filter_by(status="approved").count(),
        "suspended": Company.query.filter_by(status="suspended").count(),
        "correction": Company.query.filter_by(status="correction").count(),
    }
    return companies, status_counts


def get_company(company_id: int) -> Company:
    """Fetch a company or raise a 404 error when missing."""

    return Company.query.get_or_404(company_id)


def update_company(company: Company, payload: dict[str, str]) -> None:
    """Update editable company fields and persist changes."""

    company.name = payload.get("name", company.name)
    company.email = payload.get("email", company.email)
    company.city = payload.get("city", company.city)
    company.industry = payload.get("industry", company.industry)
    db.session.commit()


def delete_company(company: Company) -> None:
    """Remove a company and persist deletion."""

    db.session.delete(company)
    db.session.commit()


def approve_company(company: Company) -> None:
    """Mark the company as approved and send notification."""

    company.status = "approved"
    db.session.commit()
    send_company_approval_email(company)


def suspend_company(company: Company) -> None:
    """Suspend the company and inform stakeholders."""

    company.status = "suspended"
    db.session.commit()
    send_company_suspension_email(company)


def reactivate_company(company: Company) -> None:
    """Reactivate a previously suspended company and notify owners."""

    company.status = "approved"
    db.session.commit()
    send_company_reactivation_email(company)


def request_correction(company: Company) -> None:
    """Move a company into correction status and send guidance email."""

    company.status = "correction"
    db.session.commit()
    send_company_correction_email(company)
