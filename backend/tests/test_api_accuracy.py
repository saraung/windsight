"""API tests for the accuracy endpoint."""

from datetime import date

from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)


def _fake_result() -> dict:
    return {
        "from_date": date(2026, 1, 1),
        "to_date": date(2026, 1, 31),
        "decision_cutoff": None,
        "metrics": {
            "n": 10,
            "mae": 1.0,
            "rmse": 2.0,
            "bias": 0.5,
            "overforecast_percentage": 30.0,
        },
        "coverage": {
            "total_delivery_intervals": 31,
            "matched_pairs": 10,
            "missing_forecast": 1,
            "missing_actual": 0,
            "invalid_forecast": 0,
            "invalid_actual": 0,
        },
        "matches": [],
    }


def test_accuracy_returns_metrics_and_coverage(monkeypatch):
    monkeypatch.setattr(
        "app.services.analytics.run_analysis_for_period",
        lambda **kwargs: _fake_result(),
    )
    response = CLIENT.get("/api/accuracy", params={"from": "2026-01-01", "to": "2026-01-31"})
    assert response.status_code == 200
    body = response.json()
    assert body["from_date"] == "2026-01-01"
    assert body["to_date"] == "2026-01-31"
    assert body["metrics"]["n"] == 10
    assert body["coverage"]["matched_pairs"] == 10


def test_accuracy_requires_from_and_to():
    response = CLIENT.get("/api/accuracy")
    assert response.status_code == 422


def test_accuracy_rejects_from_after_to(monkeypatch):
    def _fail(**kwargs):
        raise AssertionError("service must not be called for invalid periods")

    monkeypatch.setattr("app.services.analytics.run_analysis_for_period", _fail)
    response = CLIENT.get("/api/accuracy", params={"from": "2026-01-31", "to": "2026-01-01"})
    assert response.status_code == 422
