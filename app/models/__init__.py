"""Aggregate module for exposing SQLAlchemy models."""

# This module centralizes the export of database models for convenient imports.
from app import db
from .user import User
from .company import Company
from .offer import Offer

__all__ = ["db", "User", "Company", "Offer"]
