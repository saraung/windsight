from datetime import datetime, timezone

from app.schemas.records import NormalizedRecord

RAW_FUELHH_ROW = {
    "dataset": "FUELHH",
    "publish_time": "2026-01-01T00:30:00Z",
    "start_time": "2026-01-01T00:00:00Z",
    "settlement_date": "2026-01-01",
    "settlement_period": 1,
    "fuel_type": "WIND",
    "generation_mw": 13756,
}


def test_normalize_fuelhh_row():
    record = NormalizedRecord(source="FUELHH", **RAW_FUELHH_ROW)
    assert record.source == "FUELHH"
    assert record.dataset == "FUELHH"
    assert record.publish_time == datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)
    assert record.start_time == datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert record.settlement_period == 1
    assert record.fuel_type == "WIND"
    assert record.generation_mw == 13756.0


def test_missing_generation_is_none_not_zero():
    record = NormalizedRecord(
        source="FUELHH",
        dataset="FUELHH",
        publish_time="2026-01-01T00:30:00Z",
        start_time="2026-01-01T00:00:00Z",
        generation_mw=None,
    )
    assert record.generation_mw is None


def test_invalid_generation_is_none_not_zero():
    record = NormalizedRecord(
        source="FUELHH",
        dataset="FUELHH",
        publish_time="2026-01-01T00:30:00Z",
        start_time="2026-01-01T00:00:00Z",
        generation_mw="not-a-number",
    )
    assert record.generation_mw is None


def test_timestamp_with_z_is_aware_utc():
    record = NormalizedRecord(
        source="WINDFOR",
        dataset="WINDFOR",
        publish_time="2026-01-01T02:30:00Z",
        start_time="2026-01-01T00:00:00Z",
    )
    assert record.publish_time.tzinfo is timezone.utc
    assert record.publish_time.hour == 2
