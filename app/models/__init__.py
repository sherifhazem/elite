"""Aggregate module for exposing SQLAlchemy models."""

# This module centralizes the export of database models for convenient imports.
from app.core.database import db
from .permission import Permission
from .user import User
from .company import Company
from .offer import Offer
from .notification import Notification
from .activity_log import ActivityLog
from .redemption import Redemption
from .lookup_choice import LookupChoice
from .admin_setting import AdminSetting

__all__ = [
    "db",
    "User",
    "Company",
    "Offer",
    "Notification",
    "Redemption",
    "Permission",
    "ActivityLog",
    "LookupChoice",
    "AdminSetting",
]
