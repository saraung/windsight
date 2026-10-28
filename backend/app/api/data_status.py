"""Operational data and cache status endpoint."""

from fastapi import APIRouter

from app.schemas.status import DataStatusResponse
from app.services.data_status import get_data_status

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/data-status", response_model=DataStatusResponse)
def data_status() -> DataStatusResponse:
    """Return cache freshness and source availability metadata."""
    return DataStatusResponse(**get_data_status())
