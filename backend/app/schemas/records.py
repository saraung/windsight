"""Normalized schemas for Elexon generation records."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class NormalizedRecord(BaseModel):
    """A single normalized generation record from Elexon.

    ``generation_mw`` is ``None`` when the source value was missing or could
    not be parsed; callers must not treat it as zero.
    """

    source: str = Field(..., description="Elexon dataset code (FUELHH or WINDFOR)")
    dataset: str = Field(..., description="Exact dataset code from the response")
    publish_time: datetime = Field(..., description="Forecast/publication timestamp, UTC")
    start_time: datetime = Field(..., description="Delivery interval start, UTC")
    settlement_date: date | None = None
    settlement_period: int | None = None
    fuel_type: str | None = None
    generation_mw: float | None = Field(
        default=None,
        description="Generation in megawatts; None means missing or invalid",
    )

    @field_validator("publish_time", "start_time", mode="before")
    @classmethod
    def _parse_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value

    @field_validator("generation_mw", mode="before")
    @classmethod
    def _parse_generation(cls, value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
