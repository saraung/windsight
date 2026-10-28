"""Forecast history API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.api.cutoff_params import as_validation_error, resolve_cutoff_query
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
        description="Optional absolute decision cutoff (ISO-8601 UTC).",
    ),
    cutoff_preset: str | None = Query(  # noqa: B008
        default=None,
        description="Per-delivery cutoff preset; defaults to day_ahead_noon.",
    ),
) -> ForecastHistoryResponse:
    """Return forecast vintages and the selected vintage for a delivery interval."""
    try:
        delivery = parse_utc(delivery_time)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cutoff, preset = resolve_cutoff_query(decision_cutoff, cutoff_preset)
    try:
        result = analytics.run_forecast_history(
            delivery,
            cutoff=cutoff,
            cutoff_preset=preset,
        )
    except ValueError as exc:
        raise as_validation_error(exc) from exc

    return ForecastHistoryResponse(**result)
