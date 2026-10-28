"""Forecast history API endpoints."""

from fastapi import APIRouter, Query

from app.schemas.forecast import ForecastHistoryResponse
from app.services import analytics
from app.utils.datetime_utils import parse_utc

router = APIRouter(prefix="/api", tags=["forecast-history"])


@router.get("/forecast-history", response_model=ForecastHistoryResponse)
def get_forecast_history(
    delivery_time: str = Query(  # noqa: B008
        ...,
        description="Delivery interval start (ISO-8601 UTC).",
    ),
    decision_cutoff: str | None = Query(  # noqa: B008
        default=None,
        description="Optional explicit decision cutoff (ISO-8601 UTC).",
    ),
) -> ForecastHistoryResponse:
    """Return forecast vintages and the selected vintage for a delivery interval."""
    delivery = parse_utc(delivery_time)
    cutoff = parse_utc(decision_cutoff) if decision_cutoff is not None else None
    result = analytics.run_forecast_history(delivery, cutoff=cutoff)
    return ForecastHistoryResponse(**result)
