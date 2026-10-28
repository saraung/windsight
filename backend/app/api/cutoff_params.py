"""Shared parsing and validation for decision-cutoff query parameters."""

from datetime import datetime

from fastapi import HTTPException

from app.services.forecast_selection import parse_cutoff_preset
from app.utils.datetime_utils import parse_utc


def resolve_cutoff_query(
    decision_cutoff: str | None,
    cutoff_preset: str | None,
) -> tuple[datetime | None, str | None]:
    """Validate mutually exclusive cutoff query parameters.

    Returns the parsed absolute cutoff (if any) and the validated preset
    value (if any). Invalid input is translated into HTTP 422 instead of an
    unhandled 500.
    """
    if decision_cutoff is not None and cutoff_preset is not None:
        raise HTTPException(
            status_code=422,
            detail="provide either decision_cutoff or cutoff_preset, not both",
        )

    if decision_cutoff is not None:
        try:
            return parse_utc(decision_cutoff), None
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if cutoff_preset is not None:
        try:
            parse_cutoff_preset(cutoff_preset)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return None, cutoff_preset


def as_validation_error(exc: ValueError) -> HTTPException:
    """Translate a service-layer validation error into HTTP 422."""
    return HTTPException(status_code=422, detail=str(exc))
