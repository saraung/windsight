"""API tests for the forecast-history endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.elexon_client import ElexonError

CLIENT = TestClient(app)


def test_forecast_history_returns_selected_and_vintages(monkeypatch):
    fake = {
        "delivery_time": "2026-01-15T12:00:00Z",
        "cutoff": "2026-01-14T12:00:00Z",
        "cutoff_mode": "absolute",
        "cutoff_preset": None,
        "cutoff_label": "Absolute cutoff: 2026-01-14T12:00:00+00:00",
        "cutoff_description": "One fixed decision timestamp for this delivery interval.",
        "selected": {
            "publish_time": "2026-01-14T10:00:00Z",
            "start_time": "2026-01-15T12:00:00Z",
            "generation_mw": 1100.0,
        },
        "eligible_vintages": [
            {
                "publish_time": "2026-01-14T10:00:00Z",
                "start_time": "2026-01-15T12:00:00Z",
                "generation_mw": 1100.0,
            },
        ],
        "excluded_vintages": [
            {
                "publish_time": "2026-01-14T14:00:00Z",
                "start_time": "2026-01-15T12:00:00Z",
                "generation_mw": 1200.0,
            },
        ],
    }

    def _fake(delivery_time, cutoff=None, cutoff_preset=None):
        return fake

    monkeypatch.setattr("app.services.analytics.run_forecast_history", _fake)
    response = CLIENT.get(
        "/api/forecast-history",
        params={"delivery_time": "2026-01-15T12:00Z", "decision_cutoff": "2026-01-14T12:00Z"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["selected"]["generation_mw"] == 1100.0
    assert len(body["eligible_vintages"]) == 1
    assert len(body["excluded_vintages"]) == 1


def test_forecast_history_upstream_error_returns_502(monkeypatch):
    def _boom(delivery_time, cutoff=None, cutoff_preset=None):
        raise ElexonError("upstream unavailable")

    monkeypatch.setattr("app.services.analytics.run_forecast_history", _boom)
    response = CLIENT.get("/api/forecast-history", params={"delivery_time": "2026-01-15T12:00Z"})
    assert response.status_code == 502
    assert "detail" in response.json()
