"""Typed response schema for the period overview endpoint."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.accuracy import AccuracyCoverage, AccuracyMetrics


class OverviewResponse(BaseModel):
    """Aggregate overview for a delivery period."""

    from_date: date
    to_date: date
    decision_cutoff: datetime | None = None
    delivery_intervals: int = 0
    matched_pairs: int = 0
    metrics: AccuracyMetrics = AccuracyMetrics()
    coverage: AccuracyCoverage = AccuracyCoverage()
