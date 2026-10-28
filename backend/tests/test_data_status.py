"""Tests for cache/source status reporting."""

import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.data_status import get_data_status

CLIENT = TestClient(app)


def _write_cache(path, source: str, retrieved: datetime, rows: int = 1) -> None:
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "retrieved_at_utc": retrieved.isoformat(),
        "time_range": "2026-01-01_to_2026-01-01",
        "params": {},
        "row_count": rows,
        "normalized_count": rows,
        "data": [],
    }
    (path / f"raw_{source}_2026-01-01_to_2026-01-01.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_data_status_reports_fresh_and_stale_sources(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_cache_dir", str(tmp_path))
    now = datetime.now(timezone.utc)
    cache_dir = tmp_path / "cache"
    _write_cache(cache_dir, "WINDFOR", now - timedelta(hours=1), rows=744)
    _write_cache(cache_dir, "FUELHH", now - timedelta(hours=72), rows=1488)

    result = get_data_status()

    assert result["status"] == "ok"
    assert result["cache_writable"] is True
    windfor = result["sources"]["WINDFOR"]
    fuelhh = result["sources"]["FUELHH"]
    assert windfor["cached"] is True
    assert windfor["stale"] is False
    assert windfor["row_count"] == 744
    assert fuelhh["stale"] is True
    assert fuelhh["age_hours"] > settings.cache_ttl_hours


def test_data_status_endpoint_hides_absolute_cache_path(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_cache_dir", str(tmp_path))
    response = CLIENT.get("/api/data-status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "sources" in body
    assert str(tmp_path) not in body["cache_dir"]
