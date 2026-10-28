import json
from datetime import date, datetime, timezone

import httpx
import pytest

from app.services.data_loader import DataLoader
from app.services.elexon_client import ElexonClient, ElexonHTTPError

FUELHH_ROWS = [
    {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T00:30:00Z",
        "startTime": "2026-01-01T00:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": 13756,
    },
    {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T01:00:00Z",
        "startTime": "2026-01-01T00:30:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 2,
        "fuelType": "WIND",
        "generation": None,
    },
]

WINDFOR_ROWS = [
    {
        "dataset": "WINDFOR",
        "publishTime": "2026-01-01T02:30:00Z",
        "startTime": "2026-01-01T00:00:00Z",
        "generation": 19960,
    },
]


def _make_loader(tmp_path, transport=None):
    client = ElexonClient("http://127.0.0.1:9999", transport=transport)
    return DataLoader(client=client, cache_dir=tmp_path / "cache")


def test_fetch_actuals_normalizes_rows(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/datasets/FUELHH/stream"
        assert request.url.params["settlementDateFrom"] == "2026-01-01"
        assert request.url.params["settlementDateTo"] == "2026-01-01"
        assert request.url.params["fuelType"] == "WIND"
        return httpx.Response(200, json=FUELHH_ROWS)

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    records = loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert len(records) == 2
    assert records[0].source == "FUELHH"
    assert records[0].generation_mw == 13756.0
    assert records[0].start_time == datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    # Invalid generation is preserved as None, never zero.
    assert records[1].generation_mw is None


def test_fetch_forecasts_uses_publish_window(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/datasets/WINDFOR/stream"
        assert request.url.params["publishDateTimeFrom"] == "2026-01-01T00:00:00Z"
        assert request.url.params["publishDateTimeTo"] == "2026-01-02T00:00:00Z"
        return httpx.Response(200, json=WINDFOR_ROWS)

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    records = loader.fetch_forecasts(
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
    )

    assert len(records) == 1
    assert records[0].source == "WINDFOR"
    assert records[0].generation_mw == 19960.0


def test_cache_hit_avoids_network(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network must not be called on a cache hit")

    payload = {
        "source": "FUELHH",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "time_range": "WIND_2026-01-01_to_2026-01-01",
        "params": {
            "settlementDateFrom": "2026-01-01",
            "settlementDateTo": "2026-01-01",
            "fuelType": "WIND",
        },
        "row_count": 1,
        "normalized_count": 1,
        "data": [FUELHH_ROWS[0]],
    }
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "raw_FUELHH_WIND_2026-01-01_to_2026-01-01.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    records = loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert len(records) == 1
    assert records[0].generation_mw == 13756.0


def test_stale_cache_is_refetched(tmp_path):
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=FUELHH_ROWS)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    payload = {
        "source": "FUELHH",
        "retrieved_at_utc": "2026-01-01T00:00:00+00:00",
        "time_range": "WIND_2026-01-01_to_2026-01-01",
        "params": {},
        "row_count": 1,
        "normalized_count": 1,
        "data": [FUELHH_ROWS[0]],
    }
    (cache_dir / "raw_FUELHH_WIND_2026-01-01_to_2026-01-01.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    records = loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert len(calls) == 1
    assert len(records) == 2


def test_force_refresh_refetches(tmp_path):
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=[])

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1), force_refresh=False)
    loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1), force_refresh=True)

    assert len(calls) == 2


def test_cache_file_contains_metadata(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=FUELHH_ROWS)

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    cache_files = list(tmp_path.glob("cache/raw_FUELHH_*.json"))
    assert len(cache_files) == 1
    meta = json.loads(cache_files[0].read_text(encoding="utf-8"))
    assert "retrieved_at_utc" in meta
    assert meta["row_count"] == 2
    assert meta["normalized_count"] == 2
    assert meta["params"]["fuelType"] == "WIND"
    assert len(meta["data"]) == 2


def test_fetch_actuals_propagates_client_errors(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    loader = _make_loader(tmp_path, httpx.MockTransport(handler))
    with pytest.raises(ElexonHTTPError):
        loader.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))
