"""Timestamp helpers for Elexon API parameters.

All Elexon timestamps are UTC and carried as ISO-8601 strings ending in ``Z``.
"""

from datetime import datetime, timezone


def to_utc_iso(value: datetime) -> str:
    """Render an aware datetime as an ISO-8601 UTC string ending in ``Z``."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | datetime) -> datetime:
    """Parse an Elexon timestamp into an aware UTC datetime.

    Naive timestamps are rejected because silently assuming a timezone would
    make decision-cutoff comparisons ambiguous.
    """
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise ValueError(f"timestamp must be a string or datetime, got {type(value).__name__}")

    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit UTC offset or 'Z'")

    return parsed.astimezone(timezone.utc)
