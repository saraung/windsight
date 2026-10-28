"""Typed response schema for the period overview endpoint."""

from app.schemas.accuracy import (
    AccuracyCoverage,
    AccuracyMetrics,
    DailyAccuracy,
    PeriodResponseBase,
)


class OverviewResponse(PeriodResponseBase):
    """Aggregate overview for a delivery period."""

    delivery_intervals: int = 0
    matched_pairs: int = 0
    metrics: AccuracyMetrics = AccuracyMetrics()
    daily: list[DailyAccuracy] = []
    coverage: AccuracyCoverage = AccuracyCoverage()
