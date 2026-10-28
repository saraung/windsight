"""Validation and quality helpers for normalized Elexon records."""

from collections import defaultdict
from datetime import datetime

from app.schemas.records import NormalizedRecord


def normalize_raw_row(raw: dict, source: str) -> NormalizedRecord | None:
    """Convert one raw Elexon row into a :class:`NormalizedRecord`.

    Returns ``None`` when the row cannot be normalized (for example missing
    timestamps). Invalid generation values are preserved as ``None``, never as
    zero.
    """
    try:
        return NormalizedRecord(
            source=source,
            dataset=raw.get("dataset", source),
            publish_time=raw["publishTime"],
            start_time=raw["startTime"],
            settlement_date=raw.get("settlementDate"),
            settlement_period=raw.get("settlementPeriod"),
            fuel_type=raw.get("fuelType"),
            generation_mw=raw.get("generation"),
        )
    except (KeyError, TypeError, ValueError):
        return None


def filter_fuel_type(records: list[NormalizedRecord], fuel_type: str) -> list[NormalizedRecord]:
    """Keep only records whose fuel type matches exactly."""
    return [record for record in records if record.fuel_type == fuel_type]


def find_exact_duplicates(
    records: list[NormalizedRecord],
) -> list[tuple[NormalizedRecord, NormalizedRecord]]:
    """Return pairs of records sharing ``(source, publish_time, start_time)``."""
    seen: dict[tuple[str, datetime, datetime], NormalizedRecord] = {}
    duplicates: list[tuple[NormalizedRecord, NormalizedRecord]] = []
    for record in records:
        key = (record.source, record.publish_time, record.start_time)
        if key in seen:
            duplicates.append((seen[key], record))
        else:
            seen[key] = record
    return duplicates


def delivery_coverage(records: list[NormalizedRecord]) -> dict[str, int]:
    """Count distinct delivery start times per source."""
    coverage: dict[str, set[datetime]] = defaultdict(set)
    for record in records:
        coverage[record.source].add(record.start_time)
    return {source: len(times) for source, times in coverage.items()}
