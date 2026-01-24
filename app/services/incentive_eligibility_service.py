"""Read-only eligibility evaluation for member offers."""

from __future__ import annotations

from sqlalchemy import func

from app.core.database import db
from app.models import ActivityLog, Offer
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


def _has_used_offer(member_id: int, offer_id: int) -> bool:
    """Check if the member has already successfully used this specific offer."""
    if not member_id:
        return False
    
    count = (
        ActivityLog.query.filter_by(
            action="usage_code_attempt",
            member_id=member_id,
            offer_id=offer_id
        )
        .filter(ActivityLog.result.in_(["valid", "success"]))
        .count()
    )
    return count > 0


def _get_partner_redemption_count(member_id: int, partner_id: int) -> int:
    """Return the number of successful redemptions by the member for this partner."""
    if not member_id or not partner_id:
        return 0

    return (
        ActivityLog.query.filter_by(
            action="usage_code_attempt",
            member_id=member_id,
            partner_id=partner_id
        )
        .filter(ActivityLog.result.in_(["valid", "success"]))
        .count()
    )


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
        classifications = classification_data["classifications"]
        
        if classifications:
            applied_rules.extend(
                [f"classification:{value}" for value in classifications]
            )
        if classification_data["disabled"]:
            eligible = False
            reason = "disabled_offer"

        if eligible:
            # 1. First-Time Offer Logic
            if "first_time_offer" in classifications:
                applied_rules.append("first_time_offer_check")
                # If member has used THIS offer before, they are not eligible.
                # Note: Requirement says "That same offer must never appear again to that member."
                if member_id and _has_used_offer(member_id, offer.id):
                    eligible = False
                    reason = "already_claimed"
            
            # 2. Loyalty Offer Logic
            if eligible and "loyalty_offer" in classifications:
                applied_rules.append("loyalty_check")
                # Requires at least 2 prior redemptions from THIS partner.
                if member_id:
                    redemption_count = _get_partner_redemption_count(member_id, offer.company_id)
                    if redemption_count < 2:
                        eligible = False
                        reason = "loyalty_requirement_not_met"
                else:
                     # Non-logged-in users can't prove loyalty
                    eligible = False
                    reason = "loyalty_requirement_not_met"

            # 3. Active Members Only Logic
            if eligible and ("active_members_only" in classifications or "happy_hour" in classifications):
                # Happy Hour also targets active members as per requirement
                applied_rules.append("active_member_required")
                if member_id is None or not is_member_active(member_id):
                    eligible = False
                    reason = "inactive_member"

        # Partner activity check removed to avoid cold-start deadlock
        # if eligible and _partner_rules_enabled(settings):
        #     applied_rules.append("active_partner_required")
        #     if not is_partner_active(offer.company_id):
        #         eligible = False
        #         reason = "inactive_partner"

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
    
    # Determine visibility based on eligibility failure reason
    is_visible = True
    
    if reason == "disabled_offer":
        is_visible = False
    elif reason == "already_claimed":
        # First-Time offers disappear after use
        is_visible = False
    elif reason == "loyalty_requirement_not_met":
        # Loyalty offers are hidden if requirements not met
        is_visible = False
    elif reason == "inactive_member":
         # Active-only offers are hidden for inactive members
        is_visible = False

    return {
        "is_visible": is_visible,
        "is_eligible": bool(eligibility.get("eligible")),
        "reason": reason,
        "requires_active_member": "active_member_required" in applied_rules,
        "requires_active_partner": "active_partner_required" in applied_rules,
        "is_loyalty": "loyalty_check" in applied_rules,
        "is_first_time": "first_time_offer_check" in applied_rules,
    }
