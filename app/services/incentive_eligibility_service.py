"""Read-only eligibility evaluation for member offers."""

from __future__ import annotations

from app.models import Offer
from app.modules.admin.services.admin_settings_service import get_admin_settings
from app.services.activity_evaluation_service import is_member_active, is_partner_active


def _partner_rules_enabled(settings: dict) -> bool:
    partner_rules = settings.get("partner_activity_rules", {})
    try:
        required_usages = int(partner_rules.get("required_usages", 0))
    except (TypeError, ValueError):  # pragma: no cover - defensive fallback
        required_usages = 0
    return required_usages > 0


def _classification_rules(offer: Offer, settings: dict) -> dict:
    offer_types = settings.get("offer_types", {})
    classifications = list(offer.classification_values)
    disabled = [value for value in classifications if not bool(offer_types.get(value, False))]
    return {
        "classifications": classifications,
        "disabled": disabled,
    }


def evaluate_offer_eligibility(member_id: int | None, offer_id: int) -> dict:
    """Return eligibility for a member/offer pair based on admin settings."""

    offer = Offer.query.get(offer_id)
    settings = get_admin_settings()
    applied_rules: list[str] = []
    eligible = True
    reason = "eligible"

    if offer is None:
        eligible = False
        reason = "disabled_offer"
    else:
        classification_data = _classification_rules(offer, settings)
        if classification_data["classifications"]:
            applied_rules.extend(
                [f"classification:{value}" for value in classification_data["classifications"]]
            )
        if classification_data["disabled"]:
            eligible = False
            reason = "disabled_offer"

        if eligible and "active_members_only" in classification_data["classifications"]:
            applied_rules.append("active_member_required")
            if member_id is None or not is_member_active(member_id):
                eligible = False
                reason = "inactive_member"

        if eligible and _partner_rules_enabled(settings):
            applied_rules.append("active_partner_required")
            if not is_partner_active(offer.company_id):
                eligible = False
                reason = "inactive_partner"

    if eligible:
        reason = "eligible"

    return {
        "eligible": eligible,
        "reason": reason,
        "applied_rules": applied_rules,
    }


def get_offer_runtime_flags(member_id: int | None, offer_id: int) -> dict:
    """Return runtime flags for offer visibility and eligibility in templates."""

    eligibility = evaluate_offer_eligibility(member_id, offer_id)
    applied_rules = set(eligibility.get("applied_rules", []))
    reason = eligibility.get("reason") or "eligible"
    return {
        "is_visible": reason != "disabled_offer",
        "is_eligible": bool(eligibility.get("eligible")),
        "reason": reason,
        "requires_active_member": "active_member_required" in applied_rules,
        "requires_active_partner": "active_partner_required" in applied_rules,
    }
