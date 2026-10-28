"""Forecast timeseries API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.cutoff_params import as_validation_error, resolve_cutoff_query
from app.schemas.forecast import ForecastPoint, TimeseriesResponse
from app.services import analytics

router = APIRouter(prefix="/api", tags=["timeseries"])


@router.get("/timeseries", response_model=TimeseriesResponse)
def get_timeseries(
    from_date: date = Query(  # noqa: B008
        ...,
        alias="from",
        description="Period start date (YYYY-MM-DD).",
    ),
    to_date: date = Query(  # noqa: B008
        ...,
        alias="to",
        description="Period end date (YYYY-MM-DD).",
    ),
    decision_cutoff: str | None = Query(  # noqa: B008
        default=None,
        description="Optional absolute decision cutoff (ISO-8601 UTC).",
    ),
    cutoff_preset: str | None = Query(  # noqa: B008
        default=None,
        description="Per-delivery cutoff preset; defaults to day_ahead_noon.",
    ),
) -> TimeseriesResponse:
    """Return actual vs selected forecast points for a delivery period."""
    if from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be on or before to_date")

    cutoff, preset = resolve_cutoff_query(decision_cutoff, cutoff_preset)
    try:
        result = analytics.run_analysis_for_period(
            date_from=from_date,
            date_to=to_date,
            cutoff=cutoff,
            cutoff_preset=preset,
        )
    except ValueError as exc:
        raise as_validation_error(exc) from exc

    points = []
    for match in result.get("matches") or []:
        forecast = match.get("forecast")
        actual = match.get("actual")
        forecast_mw = forecast.generation_mw if forecast is not None else None
        actual_mw = actual.generation_mw if actual is not None else None
        error_mw = None
        if forecast_mw is not None and actual_mw is not None:
            error_mw = round(forecast_mw - actual_mw, 4)
        lead_time_hours = None
        if forecast is not None:
            lead_time_hours = round(
                (match["delivery_time"] - forecast.publish_time).total_seconds() / 3600.0,
                2,
            )

        points.append(
            ForecastPoint(
                delivery_time=match["delivery_time"],
                forecast_mw=forecast_mw,
                actual_mw=actual_mw,
                error_mw=error_mw,
                lead_time_hours=lead_time_hours,
                publish_time=forecast.publish_time if forecast is not None else None,
                cutoff=match["cutoff"],
                forecast_source=forecast.source if forecast is not None else None,
                forecast_dataset=forecast.dataset if forecast is not None else None,
            )
        )

    return TimeseriesResponse(
        from_date=result["from_date"],
        to_date=result["to_date"],
        decision_cutoff=result["decision_cutoff"],
        cutoff_mode=result["cutoff_mode"],
        cutoff_preset=result["cutoff_preset"],
        cutoff_label=result["cutoff_label"],
        cutoff_description=result["cutoff_description"],
        cutoff_start=result["cutoff_start"],
        cutoff_end=result["cutoff_end"],
        points=points,
        coverage=result["coverage"],
    )
