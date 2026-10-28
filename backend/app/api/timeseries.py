"""Forecast timeseries API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.forecast import ForecastPoint, TimeseriesResponse
from app.services import analytics
from app.utils.datetime_utils import parse_utc

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
        description="Optional explicit decision cutoff (ISO-8601 UTC).",
    ),
) -> TimeseriesResponse:
    """Return actual vs selected forecast points for a delivery period."""
    if from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be on or before to_date")

    cutoff = parse_utc(decision_cutoff) if decision_cutoff is not None else None
    result = analytics.run_analysis_for_period(
        date_from=from_date,
        date_to=to_date,
        cutoff=cutoff,
    )

    points = []
    for m in result.get("matches") or []:
        fc = m.get("forecast")
        act = m.get("actual")
        points.append(
            ForecastPoint(
                delivery_time=m.get("delivery_time"),
                forecast_mw=fc.generation_mw if fc is not None else None,
                actual_mw=act.generation_mw if act is not None else None,
                publish_time=fc.publish_time if fc is not None else None,
                forecast_source=fc.source if fc is not None else None,
                forecast_dataset=fc.dataset if fc is not None else None,
            )
        )

    return TimeseriesResponse(
        from_date=result["from_date"],
        to_date=result["to_date"],
        decision_cutoff=result["decision_cutoff"],
        points=points,
        coverage=result["coverage"],
    )
