"""Aggregate module for exposing SQLAlchemy models."""

# This module centralizes the export of database models for convenient imports.
from .. import db
from .permission import Permission
from .user import User
from .company import Company
from .offer import Offer
from .notification import Notification

__all__ = ["db", "User", "Company", "Offer", "Notification", "Permission"]
