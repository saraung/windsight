from datetime import datetime, timezone

from app.schemas.records import NormalizedRecord
from app.services.data_validation import (
    delivery_coverage,
    filter_fuel_type,
    find_exact_duplicates,
    normalize_raw_row,
)

FUELHH_ROW = {
    "dataset": "FUELHH",
    "publishTime": "2026-01-01T00:30:00Z",
    "startTime": "2026-01-01T00:00:00Z",
    "settlementDate": "2026-01-01",
    "settlementPeriod": 1,
    "fuelType": "WIND",
    "generation": 13756,
}


def test_normalize_raw_row():
    record = normalize_raw_row(FUELHH_ROW, "FUELHH")
    assert record is not None
    assert record.source == "FUELHH"
    assert record.generation_mw == 13756.0


def test_normalize_raw_row_missing_timestamp():
    bad = dict(FUELHH_ROW)
    del bad["startTime"]
    assert normalize_raw_row(bad, "FUELHH") is None


def test_filter_fuel_type_keeps_only_matching():
    wind = NormalizedRecord(
        source="FUELHH",
        dataset="FUELHH",
        publish_time="2026-01-01T00:30:00Z",
        start_time="2026-01-01T00:00:00Z",
        fuel_type="WIND",
        generation_mw=100,
    )
    nuclear = NormalizedRecord(
        source="FUELHH",
        dataset="FUELHH",
        publish_time="2026-01-01T00:30:00Z",
        start_time="2026-01-01T00:00:00Z",
        fuel_type="NUCLEAR",
        generation_mw=100,
    )
    result = filter_fuel_type([wind, nuclear], "WIND")
    assert len(result) == 1
    assert result[0].fuel_type == "WIND"


def test_find_exact_duplicates():
    base = dict(
        source="WINDFOR",
        dataset="WINDFOR",
        publish_time="2026-01-01T02:30:00Z",
        start_time="2026-01-15T12:00:00Z",
    )
    first = NormalizedRecord(**base, generation_mw=100)
    second = NormalizedRecord(**base, generation_mw=110)
    third = NormalizedRecord(**base, generation_mw=120)
    dupes = find_exact_duplicates([first, second, third])
    assert len(dupes) == 2
    assert dupes[0] == (first, second)
    assert dupes[1] == (first, third)


def test_delivery_coverage_counts_distinct_starts():
    t1 = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 15, 13, tzinfo=timezone.utc)
    records = [
        NormalizedRecord(
            source="WINDFOR",
            dataset="WINDFOR",
            publish_time="2026-01-01T02:30:00Z",
            start_time=t1,
        ),
        NormalizedRecord(
            source="WINDFOR",
            dataset="WINDFOR",
            publish_time="2026-01-01T04:30:00Z",
            start_time=t1,
        ),
        NormalizedRecord(
            source="WINDFOR",
            dataset="WINDFOR",
            publish_time="2026-01-01T02:30:00Z",
            start_time=t2,
        ),
    ]
    coverage = delivery_coverage(records)
    assert coverage == {"WINDFOR": 2}
