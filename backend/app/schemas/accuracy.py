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


class AccuracyCoverage(BaseModel):
    """Coverage counts for a delivery period."""

    total_delivery_intervals: int = 0
    matched_pairs: int = 0
    missing_forecast: int = 0
    missing_actual: int = 0
    invalid_forecast: int = 0
    invalid_actual: int = 0


class AccuracyResponse(BaseModel):
    """Period-level accuracy summary."""

    from_date: date
    to_date: date
    decision_cutoff: datetime | None = None
    metrics: AccuracyMetrics = AccuracyMetrics()
    coverage: AccuracyCoverage = AccuracyCoverage()
