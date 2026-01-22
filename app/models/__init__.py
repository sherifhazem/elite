"""Aggregate module for exposing SQLAlchemy models."""

# This module centralizes the export of database models for convenient imports.
from app.core.database import db
from .permission import Permission
from .user import User
from .company import Company
from .offer import Offer, OfferClassification
from .notification import Notification
from .activity_log import ActivityLog
from .lookup_choice import LookupChoice
from .admin_setting import AdminSetting
from .usage_code import UsageCode
from .communication import Conversation, Message, Attachment

__all__ = [
    "db",
    "User",
    "Company",
    "Offer",
    "OfferClassification",
    "Notification",
    "Permission",
    "ActivityLog",
    "LookupChoice",
    "AdminSetting",
    "UsageCode",
    "Conversation",
    "Message",
    "Attachment",
]
