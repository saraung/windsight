"""Typed response schemas for forecast series, history, and selection."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.accuracy import AccuracyCoverage


class ForecastVintage(BaseModel):
    """A single forecast publication vintage for a delivery interval."""

    publish_time: datetime
    start_time: datetime
    generation_mw: float | None = None


class ForecastHistoryResponse(BaseModel):
    """Forecast vintage selection result for a single delivery interval."""

    delivery_time: datetime
    cutoff: datetime
    selected: ForecastVintage | None = None
    eligible_vintages: list[ForecastVintage] = []
    excluded_vintages: list[ForecastVintage] = []


class ForecastPoint(BaseModel):
    """Actual versus selected forecast pair for one delivery interval."""

    delivery_time: datetime
    forecast_mw: float | None = None
    actual_mw: float | None = None
    publish_time: datetime | None = None
    forecast_source: str | None = None
    forecast_dataset: str | None = None


class TimeseriesResponse(BaseModel):
    """Actual versus selected forecast series for a delivery period."""

    from_date: date
    to_date: date
    decision_cutoff: datetime | None = None
    points: list[ForecastPoint] = []
    coverage: AccuracyCoverage = AccuracyCoverage()
