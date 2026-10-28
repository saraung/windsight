"""Typed response schemas for forecast series, history, and selection."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.accuracy import AccuracyCoverage, PeriodResponseBase


class ForecastVintage(BaseModel):
    """A single forecast publication vintage for a delivery interval."""

    publish_time: datetime
    start_time: datetime
    generation_mw: float | None = None
    lead_time_hours: float | None = None


class ForecastHistoryResponse(BaseModel):
    """Forecast vintage selection result for a single delivery interval."""

    delivery_time: datetime
    cutoff: datetime
    cutoff_mode: str = "per_delivery"
    cutoff_preset: str | None = None
    cutoff_label: str = ""
    cutoff_description: str = ""
    selected: ForecastVintage | None = None
    eligible_vintages: list[ForecastVintage] = []
    excluded_vintages: list[ForecastVintage] = []


class ForecastPoint(BaseModel):
    """Actual versus selected forecast pair for one delivery interval."""

    delivery_time: datetime
    forecast_mw: float | None = None
    actual_mw: float | None = None
    error_mw: float | None = None
    lead_time_hours: float | None = None
    publish_time: datetime | None = None
    cutoff: datetime | None = None
    forecast_source: str | None = None
    forecast_dataset: str | None = None


class TimeseriesResponse(PeriodResponseBase):
    """Actual versus selected forecast series for a delivery period."""

    points: list[ForecastPoint] = []
    coverage: AccuracyCoverage = AccuracyCoverage()
