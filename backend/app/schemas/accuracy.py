"""Typed response schemas for forecast accuracy and overview endpoints."""

from datetime import date, datetime

from pydantic import BaseModel


class AccuracyMetrics(BaseModel):
    """Forecast accuracy metrics over valid matched pairs."""

    n: int = 0
    mae: float | None = None
    rmse: float | None = None
    bias: float | None = None
    overforecast_percentage: float | None = None
    underforecast_percentage: float | None = None
    error_p10: float | None = None
    error_p50: float | None = None
    error_p90: float | None = None


class DailyAccuracy(AccuracyMetrics):
    """Accuracy metrics for one UTC delivery date."""

    date: date


class AccuracyCoverage(BaseModel):
    """Coverage counts for a delivery period.

    Categories are counted independently. An interval can be missing both an
    actual and a forecast, so the counts do not necessarily sum to
    ``total_delivery_intervals``.
    """

    total_delivery_intervals: int = 0
    matched_pairs: int = 0
    missing_forecast: int = 0
    missing_actual: int = 0
    missing_both: int = 0
    invalid_forecast: int = 0
    invalid_actual: int = 0
    incomplete_actual: int = 0
    coverage_percentage: float | None = None


class PeriodResponseBase(BaseModel):
    """Shared period and decision-cutoff response fields."""

    from_date: date
    to_date: date
    decision_cutoff: datetime | None = None
    cutoff_mode: str = "per_delivery"
    cutoff_preset: str | None = None
    cutoff_label: str = ""
    cutoff_description: str = ""
    cutoff_start: datetime | None = None
    cutoff_end: datetime | None = None


class AccuracyResponse(PeriodResponseBase):
    """Period-level accuracy summary."""

    metrics: AccuracyMetrics = AccuracyMetrics()
    daily: list[DailyAccuracy] = []
    coverage: AccuracyCoverage = AccuracyCoverage()
