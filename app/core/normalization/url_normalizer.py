"""Centralized URL normalization utilities."""

from __future__ import annotations

def normalize_url(raw: str) -> str:
    """Normalize user-submitted URLs with a consistent strategy."""

    if raw is None:
        return ""

    candidate = raw.strip()
    if candidate == "":
        return ""

    lower = candidate.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return candidate
    if candidate.startswith("www."):
        return f"https://{candidate}"
    if candidate[:1].isdigit():
        return f"https://www.{candidate}"
    if "." in candidate:
        return f"https://{candidate}"

    return candidate


__all__ = ["normalize_url"]
