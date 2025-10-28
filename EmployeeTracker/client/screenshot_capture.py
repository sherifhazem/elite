"""Placeholder module for screenshot capture functionality on the client."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def capture_screenshot(output_path: Optional[Path] = None) -> Path:
    """Capture a screenshot and return the file path.

    This is a placeholder implementation meant to document the intended
    integration point. The real implementation should save the captured
    image to ``output_path`` (when provided) or to a sensible default
    within the client's storage directory.
    """
    raise NotImplementedError("Screenshot capture is not implemented yet")
