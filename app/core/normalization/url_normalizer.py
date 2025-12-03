"""Centralized URL normalization utilities."""

from __future__ import annotations


def normalize_url(raw: str) -> str:
    """Normalize user-submitted URLs with a consistent strategy."""

    value = "" if raw is None else raw.strip()
    if value == "":
        return ""

    if value.startswith("http"):
        return value
    if value.startswith("www."):
        return f"https://{value}"
    if value[:1].isdigit():
        return f"https://www.{value}"
    if "." in value:
        return f"https://{value}"

    return value


__all__ = ["normalize_url"]
