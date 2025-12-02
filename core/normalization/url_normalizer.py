"""Centralized URL normalization utilities."""

from __future__ import annotations

import re

_SCHEMES: tuple[str, ...] = ("http://", "https://", "ftp://")
_INVALID_CHARS_PATTERN = re.compile(r"[\\s<>\"'{}|\\^`]")


def _has_scheme(candidate: str) -> bool:
    lower_candidate = candidate.lower()
    return lower_candidate.startswith(_SCHEMES)


def _strip_scheme(candidate: str) -> str:
    lowered = candidate.lower()
    for scheme in _SCHEMES:
        if lowered.startswith(scheme):
            return candidate[len(scheme) :]
    return candidate


def _contains_invalid_characters(candidate: str) -> bool:
    return bool(_INVALID_CHARS_PATTERN.search(candidate))


def _looks_like_domain(candidate: str) -> bool:
    trimmed = candidate.strip().strip("/")
    if len(trimmed) < 3:
        return False
    if "." not in trimmed:
        return False
    return True


def _is_plausible_url(candidate: str) -> bool:
    if not candidate:
        return False
    if _contains_invalid_characters(candidate):
        return False
    without_scheme = _strip_scheme(candidate)
    return _looks_like_domain(without_scheme)


def _should_prefix_https(raw: str) -> bool:
    if not raw:
        return False
    if raw.startswith("www."):
        return True
    return "." in raw and not _has_scheme(raw)


def normalize_url(raw: str) -> str:
    """Return a normalized URL string following project-wide rules.

    - Empty input returns an empty string.
    - Existing schemes (http, https, ftp) are preserved.
    - Values starting with "www." or containing a dot without a scheme are prefixed with ``https://``.
    - Obvious non-URLs (too short, missing dots, invalid characters) are returned unchanged so validation can fail later.
    """

    if raw is None:
        return ""

    candidate = raw.strip()
    if candidate == "":
        return ""

    normalized = candidate
    if not _has_scheme(candidate) and _should_prefix_https(candidate):
        normalized = f"https://{candidate}"

    if not _is_plausible_url(normalized):
        return candidate

    return normalized


__all__ = ["normalize_url"]
