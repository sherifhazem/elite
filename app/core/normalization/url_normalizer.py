"""Centralized URL normalization utilities."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_SCHEMES: tuple[str, ...] = ("http://", "https://")
_INVALID_CHARS_PATTERN = re.compile(r"[\s<>\"'{}|\\^`]")


def _should_prefix_https(raw: str, has_any_scheme: bool) -> bool:
    if not raw or has_any_scheme:
        return False
    if raw.startswith("www."):
        return True
    return "." in raw


def _is_parsable_url(candidate: str) -> bool:
    if not candidate or _INVALID_CHARS_PATTERN.search(candidate):
        return False
    parsed = urlparse(candidate)
    return bool(parsed.netloc)


def normalize_url(raw: str) -> str:
    """Normalize user-submitted URLs with a consistent strategy.

    - If empty: return an empty string.
    - If the value already starts with ``http://`` or ``https://`` keep it.
    - If it starts with ``www.`` or contains a dot with no scheme, prefix ``https://``.
    - Strip surrounding whitespace before processing.
    - If the resulting value cannot be parsed as a URL (missing ``netloc`` or invalid characters),
      return the original input so downstream validation can flag it.
    """

    if raw is None:
        return ""

    candidate = raw.strip()
    if candidate == "":
        return ""

    parsed = urlparse(candidate)
    has_any_scheme = bool(parsed.scheme)
    normalized = candidate
    if candidate.lower().startswith(_SCHEMES):
        normalized = candidate
    elif _should_prefix_https(candidate, has_any_scheme):
        normalized = f"https://{candidate}"

    if not _is_parsable_url(normalized):
        return candidate

    return normalized


__all__ = ["normalize_url"]
