"""Central registry exports for choices used across the platform."""

from .registry import (
    CITIES,
    INDUSTRIES,
    get_cities,
    get_industries,
    validate_choice,
)

__all__ = [
    "CITIES",
    "INDUSTRIES",
    "get_cities",
    "get_industries",
    "validate_choice",
]
