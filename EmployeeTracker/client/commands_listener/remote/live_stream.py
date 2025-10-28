"""Utilities for orchestrating a lightweight live screen stream."""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

LOGGER = logging.getLogger(__name__)

# يعتمد البث على التقاط صور الشاشة بشكل متتالٍ وإرسالها بسرعة عالية،
# في أسلوب يشبه MJPEG أو بث صور مجزأة كل ثانية لتمثيل مشاركة الشاشة.


def start_stream(duration_seconds: Optional[int] = None, quality: str = "medium") -> None:
    """Start a pseudo live stream of the current screen.

    Parameters
    ----------
    duration_seconds:
        مدة البث بالثواني. إذا كانت ``None`` يستمر حتى يتم استدعاء
        ``stop_stream``.
    quality:
        مؤشر نصي يسمح بتخفيض الدقة أو معدل الإطارات ("low", "medium", "high").
    """

    LOGGER.info(
        "Starting live stream with duration=%s, quality=%s", duration_seconds, quality
    )
    _StreamingLoop(duration_seconds=duration_seconds, quality=quality).start()


def stop_stream() -> None:
    """Request graceful stop for the active stream if available."""

    _StreamingLoop.stop_active()


class _StreamingLoop(threading.Thread):
    """Worker thread that simulates streaming frames to the server."""

    _active_loop: Optional["_StreamingLoop"] = None

    def __init__(self, *, duration_seconds: Optional[int], quality: str) -> None:
        super().__init__(daemon=True)
        self.duration_seconds = duration_seconds
        self.quality = quality
        self._stop_event = threading.Event()

    @classmethod
    def stop_active(cls) -> None:
        if cls._active_loop is not None:
            LOGGER.info("Stopping live stream")
            cls._active_loop._stop_event.set()
            cls._active_loop = None

    def run(self) -> None:  # noqa: D401
        """Thread loop that emits frames periodically."""

        _StreamingLoop._active_loop = self
        start_time = time.monotonic()
        frame_interval = _quality_to_interval(self.quality)

        while not self._stop_event.is_set():
            # TODO: integrate with real screen capture + transport layer.
            LOGGER.debug("Streaming frame at quality=%s", self.quality)
            time.sleep(frame_interval)

            if self.duration_seconds is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= self.duration_seconds:
                    LOGGER.info("Live stream duration reached (%ss)", self.duration_seconds)
                    break

        LOGGER.info("Live stream finished")
        _StreamingLoop._active_loop = None


def _quality_to_interval(quality: str) -> float:
    """Translate quality levels to frame intervals (seconds)."""

    quality_map = {
        "high": 0.25,
        "medium": 0.5,
        "low": 1.0,
    }
    return quality_map.get(quality, 0.5)
