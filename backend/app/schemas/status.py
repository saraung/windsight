"""Typed response schemas for source and cache status."""

from datetime import datetime

from pydantic import BaseModel


class SourceStatus(BaseModel):
    """Cache status for one Elexon source dataset."""

    source: str
    cached: bool = False
    files: int = 0
    last_retrieved_utc: datetime | None = None
    age_hours: float | None = None
    stale: bool = False
    row_count: int | None = None
    normalized_count: int | None = None


class DataStatusResponse(BaseModel):
    """Operational status for the backend's Elexon cache."""

    status: str = "ok"
    checked_at_utc: datetime
    cache_dir: str
    cache_writable: bool
    cache_ttl_hours: float
    sources: dict[str, SourceStatus]
