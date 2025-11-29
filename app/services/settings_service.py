"""Compatibility shim exposing settings helpers via the legacy import path."""

from app.modules.admin.services.settings_service import (
    add_item,
    delete_item,
    get_all_settings,
    get_list,
    get_section,
    save_list,
    update_item,
    update_settings,
)

__all__ = [
    "get_all_settings",
    "get_section",
    "update_settings",
    "get_list",
    "save_list",
    "add_item",
    "delete_item",
    "update_item",
]
