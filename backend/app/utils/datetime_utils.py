"""Timestamp helpers for Elexon API parameters.

All Elexon timestamps are UTC and carried as ISO-8601 strings ending in ``Z``.
"""

from datetime import datetime, timezone


def to_utc_iso(value: datetime) -> str:
    """Render an aware datetime as an ISO-8601 UTC string ending in ``Z``."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value) -> datetime:
    """Parse an Elexon timestamp into an aware UTC datetime."""
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value
