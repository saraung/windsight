from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import accuracy, data_status, forecast_history, health, overview, timeseries
from app.config import settings
from app.services.elexon_client import ElexonError

app = FastAPI(title=settings.app_name)


if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )


app.include_router(health.router)
app.include_router(overview.router)
app.include_router(accuracy.router)
app.include_router(timeseries.router)
app.include_router(forecast_history.router)
app.include_router(data_status.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "health": "/api/health",
        "docs": "/docs",
    }


@app.exception_handler(ElexonError)
async def elexon_error_handler(request: Request, exc: ElexonError) -> JSONResponse:
    """Translate Elexon upstream failures into explicit HTTP error responses."""
    return JSONResponse(status_code=502, content={"detail": f"Elexon upstream error: {exc}"})
