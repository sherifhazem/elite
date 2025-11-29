# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Service helpers powering the offer redemption workflow."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import qrcode
from flask import current_app
from qrcode.constants import ERROR_CORRECT_H
from sqlalchemy.orm import joinedload

from app.core.database import db
from app.models import Offer, Redemption, User
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
    """Emit standardized observability events for redemption services."""
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


def _generate_unique_code(length: int = 12) -> str:
    """Return a unique redemption code of the requested length."""

    attempts = 0
    while attempts < 20:
        candidate = uuid.uuid4().hex.upper()[:length]
        if not Redemption.query.filter_by(redemption_code=candidate).first():
            return candidate
        attempts += 1
    raise RuntimeError("Unable to generate a unique redemption code.")


def _qr_storage_directory() -> str:
    """Return the absolute directory path used to store QR code images."""

    static_root = os.path.join(current_app.root_path, "modules", "members", "static")
    qr_dir = os.path.join(static_root, "qrcodes")
    os.makedirs(qr_dir, exist_ok=True)
    return qr_dir


def _refresh_expiration(redemption: Redemption) -> bool:
    """Expire a redemption in-place when its validity window has passed."""

    if redemption.status == "pending" and redemption.is_expired():
        redemption.mark_expired()
        db.session.flush()
        return True
    return False


def _serialize(redemption: Redemption) -> dict:
    """Return a JSON-serializable representation of a redemption."""

    return {
        "code": redemption.redemption_code,
        "status": redemption.status,
        "created_at": redemption.created_at.isoformat() if redemption.created_at else None,
        "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
        "expires_at": redemption.expires_at.isoformat() if redemption.expires_at else None,
        "offer_id": redemption.offer_id,
        "company_id": redemption.company_id,
        "user_id": redemption.user_id,
        "qr_token": redemption.qr_token,
    }


def create_redemption(user_id: int, offer_id: int) -> Redemption:
    """Create a fresh redemption for the given user and offer combination."""

    user = User.query.get(user_id)
    if user is None:
        raise ValueError("User not found.")
    offer = Offer.query.get(offer_id)
    if offer is None:
        raise ValueError("Offer not found.")
    if offer.company_id is None:
        raise ValueError("Offer is not linked to a company.")

    latest = (
        Redemption.query.filter_by(user_id=user_id, offer_id=offer_id)
        .order_by(Redemption.created_at.desc())
        .first()
    )
    if latest is not None:
        if latest.status == "redeemed":
            raise ValueError("This offer has already been redeemed by the user.")
        if not latest.is_expired():
            raise ValueError("An active redemption already exists for this offer.")
        latest.mark_expired()

    code = _generate_unique_code()
    redemption = Redemption(
        user_id=user_id,
        offer_id=offer_id,
        company_id=offer.company_id,
        redemption_code=code,
        status="pending",
    )
    db.session.add(redemption)
    db.session.flush()
    generate_qr_token(code, commit=False)
    db.session.commit()
    return redemption


def get_redemption_status(code: str) -> Optional[dict]:
    """Return the serialized redemption state for the provided code."""

    redemption = Redemption.query.filter_by(redemption_code=code).first()
    if redemption is None:
        return None
    changed = _refresh_expiration(redemption)
    if changed:
        db.session.commit()
    return _serialize(redemption)


def mark_redeemed(
    code: str,
    *,
    company_id: Optional[int] = None,
    qr_token: Optional[str] = None,
) -> Redemption:
    """Mark a redemption as redeemed if it belongs to the provided company."""

    redemption = Redemption.query.filter_by(redemption_code=code).first()
    if redemption is None:
        raise LookupError("Redemption not found.")

    if company_id is not None and redemption.company_id != company_id:
        raise PermissionError("This redemption does not belong to the company.")

    if redemption.qr_token and qr_token and redemption.qr_token != qr_token:
        raise ValueError("QR token mismatch.")

    if _refresh_expiration(redemption):
        db.session.commit()
        raise ValueError("The redemption code has expired.")

    if redemption.status == "redeemed":
        return redemption

    redemption.mark_redeemed()
    db.session.commit()
    return redemption


def generate_qr_token(
    code: str,
    *,
    commit: bool = True,
    regenerate: bool = False,
) -> Redemption:
    """Generate (or reuse) a QR token and image for the provided code."""

    redemption = Redemption.query.filter_by(redemption_code=code).first()
    if redemption is None:
        raise LookupError("Redemption not found.")

    if not redemption.qr_token or regenerate:
        redemption.qr_token = str(uuid.uuid4())

    payload = json.dumps({"code": redemption.redemption_code, "token": redemption.qr_token})
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    directory = _qr_storage_directory()
    file_path = os.path.join(directory, f"{redemption.redemption_code}.png")
    image.save(file_path)

    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return redemption


def list_user_redemptions(user_id: int) -> Iterable[Redemption]:
    """Return all redemptions for a user while synchronizing expiration state."""

    redemptions = (
        Redemption.query.filter_by(user_id=user_id)
        .order_by(Redemption.created_at.desc())
        .all()
    )
    changed = False
    for redemption in redemptions:
        changed = _refresh_expiration(redemption) or changed
    if changed:
        db.session.commit()
    return redemptions


def list_user_redemptions_with_context(user_id: int) -> List[Dict[str, object]]:
    """Return member redemptions enriched with offer and company data."""

    query = (
        Redemption.query.filter_by(user_id=user_id)
        .options(
            joinedload(Redemption.offer).joinedload(Offer.company),
            joinedload(Redemption.company),
        )
        .order_by(Redemption.created_at.desc())
    )
    records: List[Redemption] = query.all()
    changed = False
    payload: List[Dict[str, object]] = []
    for redemption in records:
        changed = _refresh_expiration(redemption) or changed
        offer = redemption.offer
        company = offer.company if offer and offer.company else redemption.company
        payload.append(
            {
                "id": redemption.id,
                "status": redemption.status,
                "redemption_code": redemption.redemption_code,
                "created_at": redemption.created_at,
                "redeemed_at": redemption.redeemed_at,
                "expires_at": redemption.expires_at,
                "offer": {
                    "id": offer.id if offer else redemption.offer_id,
                    "title": offer.title if offer else f"Offer #{redemption.offer_id}",
                    "description": offer.description if offer else "",
                },
                "company": {
                    "id": company.id if company else redemption.company_id,
                    "name": company.name if company else "شريك ELITE",
                    "summary": (company.description or "")[:140] if company else "",
                    "description": (company.description or "") if company else "",
                },
            }
        )
    if changed:
        db.session.commit()
    return payload


def list_company_redemptions(
    company_id: int,
    *,
    offer_id: Optional[int] = None,
    status: Optional[str] = None,
    date_range: Optional[Tuple[datetime | None, datetime | None]] = None,
    limit: Optional[int] = None,
) -> List[Redemption]:
    """Return company-scoped redemptions filtered by optional criteria."""

    query = (
        Redemption.query.filter_by(company_id=company_id)
        .options(
            joinedload(Redemption.offer),
            joinedload(Redemption.user),
        )
        .order_by(Redemption.created_at.desc())
    )

    if offer_id:
        query = query.filter(Redemption.offer_id == offer_id)
    if status:
        query = query.filter(Redemption.status == status)
    if date_range:
        start, end = date_range
        if start:
            query = query.filter(Redemption.created_at >= start)
        if end:
            query = query.filter(Redemption.created_at <= end)
    if limit:
        query = query.limit(limit)
    redemptions = query.all()
    changed = False
    for redemption in redemptions:
        changed = _refresh_expiration(redemption) or changed
    if changed:
        db.session.commit()
    return redemptions


__all__ = [
    "create_redemption",
    "get_redemption_status",
    "mark_redeemed",
    "generate_qr_token",
    "list_user_redemptions",
    "list_user_redemptions_with_context",
    "list_company_redemptions",
]
