# LINKED: Added admin-managed dropdown system for Cities and Industries.
# Introduced unified Settings Service and admin UI for dynamic list management.
# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.
"""Form package exposing reusable WTForms classes."""

from .company_registration_form import CITY_CHOICES, INDUSTRY_CHOICES, CompanyRegistrationForm

__all__ = ["CompanyRegistrationForm", "INDUSTRY_CHOICES", "CITY_CHOICES"]
