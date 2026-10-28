"""Accuracy API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.cutoff_params import as_validation_error, resolve_cutoff_query
from app.schemas.accuracy import AccuracyResponse
from app.services import analytics

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
        description="Optional absolute decision cutoff (ISO-8601 UTC).",
    ),
    cutoff_preset: str | None = Query(  # noqa: B008
        default=None,
        description="Per-delivery cutoff preset; defaults to day_ahead_noon.",
    ),
) -> AccuracyResponse:
    """Return forecast accuracy metrics and coverage for a delivery period."""
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

    return AccuracyResponse(
        from_date=result["from_date"],
        to_date=result["to_date"],
        decision_cutoff=result["decision_cutoff"],
        cutoff_mode=result["cutoff_mode"],
        cutoff_preset=result["cutoff_preset"],
        cutoff_label=result["cutoff_label"],
        cutoff_description=result["cutoff_description"],
        cutoff_start=result["cutoff_start"],
        cutoff_end=result["cutoff_end"],
        metrics=result["metrics"],
        daily=result["daily"],
        coverage=result["coverage"],
    )
