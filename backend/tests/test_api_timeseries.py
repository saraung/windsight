"""API tests for the timeseries endpoint."""

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.records import NormalizedRecord

CLIENT = TestClient(app)


def _fake_result() -> dict:
    return {
        "from_date": date(2026, 1, 15),
        "to_date": date(2026, 1, 15),
        "decision_cutoff": None,
        "metrics": {
            "n": 1,
            "mae": 10.0,
            "rmse": 10.0,
            "bias": 10.0,
            "overforecast_percentage": 100.0,
        },
        "coverage": {
            "total_delivery_intervals": 1,
            "matched_pairs": 1,
            "missing_forecast": 0,
            "missing_actual": 0,
            "invalid_forecast": 0,
            "invalid_actual": 0,
        },
        "matches": [
            {
                "delivery_time": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
                "actual": NormalizedRecord(
                    source="FUELHH",
                    dataset="FUELHH",
                    publish_time=datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc),
                    start_time=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
                    generation_mw=90.0,
                ),
                "forecast": NormalizedRecord(
                    source="WINDFOR",
                    dataset="WINDFOR",
                    publish_time=datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc),
                    start_time=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
                    generation_mw=100.0,
                ),
                "cutoff": datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc),
                "forecast_eligible": True,
            },
        ],
    }


def test_timeseries_returns_points(monkeypatch):
    monkeypatch.setattr(
        "app.services.analytics.run_analysis_for_period", lambda **kwargs: _fake_result()
    )
    response = CLIENT.get("/api/timeseries", params={"from": "2026-01-15", "to": "2026-01-15"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["points"]) == 1
    point = body["points"][0]
    assert point["forecast_mw"] == 100.0
    assert point["actual_mw"] == 90.0
    assert point["forecast_source"] == "WINDFOR"
