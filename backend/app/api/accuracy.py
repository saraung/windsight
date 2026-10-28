"""Accuracy API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.accuracy import AccuracyResponse
from app.services import analytics
from app.utils.datetime_utils import parse_utc

router = APIRouter(prefix="/api", tags=["accuracy"])


@router.get("/accuracy", response_model=AccuracyResponse)
def get_accuracy(
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
) -> AccuracyResponse:
    """Return forecast accuracy metrics and coverage for a delivery period."""
    if from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be on or before to_date")

    cutoff = parse_utc(decision_cutoff) if decision_cutoff is not None else None
    result = analytics.run_analysis_for_period(
        date_from=from_date,
        date_to=to_date,
        cutoff=cutoff,
    )
    return AccuracyResponse(
        from_date=result["from_date"],
        to_date=result["to_date"],
        decision_cutoff=result["decision_cutoff"],
        metrics=result["metrics"],
        coverage=result["coverage"],
    )
