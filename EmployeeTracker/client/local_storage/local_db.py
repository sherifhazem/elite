"""Interfaces for storing encrypted data on the local device.

This module is intended to coordinate secure persistence of temporary data. The
preferred backend is SQLite (one table per data type) with payload columns kept
encrypted via the helpers in :mod:`local_storage.encryptor`. If SQLite is not
available, a JSON-file fallback can be considered, but every record must be
stored in encrypted form either way.

Screenshots should remain as files under a dedicated folder. Only their file
paths and associated metadata get persisted here, and those values must also be
encrypted before writing into the database layer.
"""

from typing import Iterable, List


# Database initialization helpers ------------------------------------------------
# Later implementation should create tables (e.g., activity_logs, idle_periods,
# screenshots) and handle migrations, ensuring that sensitive fields are stored
# as BLOBs containing encrypted bytes. Connections should be managed carefully
# to avoid leaks.


def store_activity_log(log_data):
    """Persist a unit of activity tracking data.

    Expected workflow:
        1. Normalize ``log_data`` into a dictionary ready for serialization.
        2. Call :func:`encryptor.encrypt_data` before inserting into SQLite.
        3. Save the encrypted blob alongside timestamps and sync flags.
    """
    raise NotImplementedError("Local activity log storage not yet implemented")


def store_idle_period(start_time, end_time):
    """Record an idle period captured by the monitoring service.

    Both ``start_time`` and ``end_time`` should be serialized into an object,
    encrypted, and inserted into the idle-periods table (or dedicated file).
    """
    raise NotImplementedError("Idle period storage not yet implemented")


def store_screenshot_info(file_path, timestamp):
    """Persist metadata about a captured screenshot.

    The actual image file remains on disk; ``file_path`` and ``timestamp`` get
    bundled into a payload, encrypted, and stored for later sync.
    """
    raise NotImplementedError("Screenshot metadata storage not yet implemented")


def get_unsynced_data() -> List[dict]:
    """Return the collection of unsynced records across all tables.

    Implementation notes:
        * Query each table for rows marked as not yet synced.
        * Decrypt their payloads via :func:`encryptor.decrypt_data`.
        * Yield dictionaries ready for transmission when connectivity allows.
    """
    raise NotImplementedError("Fetching unsynced data not yet implemented")


def mark_data_as_synced(ids: Iterable[int]):
    """Mark records as synced after remote transmission succeeds.

    This should accept record identifiers grouped by table or include enough
    context to update the corresponding rows. Consider wrapping updates in a
    transaction to maintain data integrity.
    """
    raise NotImplementedError("Sync flag update not yet implemented")
