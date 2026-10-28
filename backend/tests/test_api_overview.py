"""API tests for the overview endpoint."""

from datetime import date

from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)


def test_overview_returns_headline_counts(monkeypatch):
    fake = {
        "from_date": date(2026, 1, 1),
        "to_date": date(2026, 1, 31),
        "decision_cutoff": None,
        "cutoff_mode": "per_delivery",
        "cutoff_preset": "day_ahead_noon",
        "cutoff_label": "Day-ahead noon",
        "cutoff_description": "Forecast published by 12:00 the day before delivery.",
        "cutoff_start": None,
        "cutoff_end": None,
        "metrics": {"n": 10, "mae": 1.0, "rmse": 2.0, "bias": 0.5, "overforecast_percentage": 30.0},
        "daily": [],
        "coverage": {
            "total_delivery_intervals": 31,
            "matched_pairs": 10,
            "missing_forecast": 1,
            "missing_actual": 0,
            "missing_both": 0,
            "invalid_forecast": 0,
            "invalid_actual": 0,
            "incomplete_actual": 0,
            "coverage_percentage": 32.2581,
        },
        "matches": [],
    }
    monkeypatch.setattr("app.services.analytics.run_analysis_for_period", lambda **kwargs: fake)
    response = CLIENT.get("/api/overview", params={"from": "2026-01-01", "to": "2026-01-31"})
    assert response.status_code == 200
    body = response.json()
    assert body["delivery_intervals"] == 31
    assert body["matched_pairs"] == 10
    assert body["metrics"]["n"] == 10
