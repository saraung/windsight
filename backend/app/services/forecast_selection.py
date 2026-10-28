"""Pure forecast-vintage selection logic.

Selects, for each delivery interval, the latest forecast that had been
published at or before a chosen decision cutoff. No look-ahead bias: a
forecast published *after* the cutoff is never eligible, regardless of how
much more accurate it might be.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from enum import Enum

from app.schemas.records import NormalizedRecord


class CutoffPreset(str, Enum):
    """Supported per-delivery decision-cutoff rules."""

    DAY_AHEAD_NOON = "day_ahead_noon"
    DAY_AHEAD_MIDNIGHT = "day_ahead_midnight"
    HOURS_24 = "hours_24"
    HOURS_12 = "hours_12"
    HOURS_2 = "hours_2"
    HOURS_1 = "hours_1"


DEFAULT_CUTOFF_PRESET = CutoffPreset.DAY_AHEAD_NOON

CUTOFF_LABELS: dict[CutoffPreset, str] = {
    CutoffPreset.DAY_AHEAD_NOON: "Day-ahead 12:00 UTC (D-1)",
    CutoffPreset.DAY_AHEAD_MIDNIGHT: "Day-ahead 00:00 UTC (D-1)",
    CutoffPreset.HOURS_24: "24 hours before delivery",
    CutoffPreset.HOURS_12: "12 hours before delivery",
    CutoffPreset.HOURS_2: "2 hours before delivery",
    CutoffPreset.HOURS_1: "1 hour before delivery",
}

CUTOFF_DESCRIPTIONS: dict[CutoffPreset, str] = {
    CutoffPreset.DAY_AHEAD_NOON: "Noon UTC on the calendar day before delivery.",
    CutoffPreset.DAY_AHEAD_MIDNIGHT: "Midnight UTC at the start of the day before delivery.",
    CutoffPreset.HOURS_24: "Exactly 24 hours before the delivery interval starts.",
    CutoffPreset.HOURS_12: "Exactly 12 hours before the delivery interval starts.",
    CutoffPreset.HOURS_2: "Exactly 2 hours before the delivery interval starts.",
    CutoffPreset.HOURS_1: "Exactly 1 hour before the delivery interval starts.",
}


def parse_cutoff_preset(value: str | CutoffPreset | None) -> CutoffPreset:
    """Validate a query-string cutoff preset, defaulting to day-ahead noon."""
    if value is None:
        return DEFAULT_CUTOFF_PRESET
    if isinstance(value, CutoffPreset):
        return value
    try:
        return CutoffPreset(value)
    except ValueError as exc:
        allowed = ", ".join(preset.value for preset in CutoffPreset)
        raise ValueError(f"invalid cutoff_preset {value!r}; expected one of: {allowed}") from exc


def cutoff_for_preset(preset: CutoffPreset | str, delivery_time: datetime) -> datetime:
    """Return the cutoff timestamp for one delivery interval under ``preset``."""
    preset = parse_cutoff_preset(preset)
    delivery = delivery_time.astimezone(timezone.utc)

    if preset is CutoffPreset.DAY_AHEAD_NOON:
        cutoff_date = delivery.date() - timedelta(days=1)
        return datetime(
            cutoff_date.year,
            cutoff_date.month,
            cutoff_date.day,
            12,
            0,
            tzinfo=timezone.utc,
        )
    if preset is CutoffPreset.DAY_AHEAD_MIDNIGHT:
        cutoff_date = delivery.date() - timedelta(days=1)
        return datetime(
            cutoff_date.year,
            cutoff_date.month,
            cutoff_date.day,
            0,
            0,
            tzinfo=timezone.utc,
        )
    if preset is CutoffPreset.HOURS_24:
        return delivery - timedelta(hours=24)
    if preset is CutoffPreset.HOURS_12:
        return delivery - timedelta(hours=12)
    if preset is CutoffPreset.HOURS_2:
        return delivery - timedelta(hours=2)
    if preset is CutoffPreset.HOURS_1:
        return delivery - timedelta(hours=1)
    raise ValueError(f"unsupported cutoff preset: {preset!r}")


def cutoff_label(preset: CutoffPreset | str | None) -> str:
    """Human-readable label for a cutoff preset."""
    return CUTOFF_LABELS[parse_cutoff_preset(preset)]


def cutoff_description(preset: CutoffPreset | str | None) -> str:
    """Longer explanation for a cutoff preset."""
    return CUTOFF_DESCRIPTIONS[parse_cutoff_preset(preset)]


def default_cutoff(delivery_time: datetime) -> datetime:
    """Default decision cutoff: D-1 12:00 UTC.

    For a delivery at ``delivery_time``, the cutoff is noon UTC on the
    calendar day before the delivery date. This is a sensible day-ahead
    procurement assumption; it is configurable and must be made visible to
    the user.
    """
    return cutoff_for_preset(DEFAULT_CUTOFF_PRESET, delivery_time)


def make_cutoff_func(
    preset: CutoffPreset | str | None = None,
    absolute: datetime | None = None,
) -> Callable[[datetime], datetime]:
    """Build a cutoff function for either a preset or one absolute timestamp."""
    if absolute is not None:
        return lambda _delivery: absolute
    resolved = parse_cutoff_preset(preset)
    return lambda delivery: cutoff_for_preset(resolved, delivery)


def select_latest_forecast(
    forecasts: list[NormalizedRecord],
    delivery_time: datetime,
    cutoff: datetime,
) -> NormalizedRecord | None:
    """Return the latest forecast for ``delivery_time`` with ``publish_time <= cutoff``.

    Eligibility:
    - ``start_time`` must match ``delivery_time`` exactly.
    - ``publish_time`` must be at or before ``cutoff``.

    Selection:
    - Among eligible records, the greatest ``publish_time`` wins.
    - If multiple records share the same greatest ``publish_time`` (exact
      duplicates), the deterministic tie-break is the greatest
      ``generation_mw`` (with ``None`` treated as lowest), then the first
      record in input order. This keeps behaviour reproducible.

    Returns ``None`` when no eligible forecast exists. Callers must treat
    that as missing data, never substitute a later forecast.
    """
    eligible = [f for f in forecasts if f.start_time == delivery_time and f.publish_time <= cutoff]
    if not eligible:
        return None

    def sort_key(f: NormalizedRecord) -> tuple[datetime, float]:
        gen = f.generation_mw if f.generation_mw is not None else float("-inf")
        return (f.publish_time, gen)

    eligible.sort(key=sort_key, reverse=True)
    return eligible[0]


def select_for_delivery_times(
    forecasts: list[NormalizedRecord],
    delivery_times: Iterable[datetime],
    cutoff_func: Callable[[datetime], datetime] = default_cutoff,
) -> list[dict]:
    """Select one forecast for every requested delivery time.

    Returns a list of match dictionaries with keys ``delivery_time``,
    ``forecast``, ``cutoff``, and ``forecast_eligible``. The caller attaches
    the actual record for each interval.
    """
    forecasts_by_start: dict[datetime, list[NormalizedRecord]] = defaultdict(list)
    for forecast in forecasts:
        forecasts_by_start[forecast.start_time].append(forecast)

    matches: list[dict] = []
    for delivery_time in sorted(set(delivery_times)):
        cutoff = cutoff_func(delivery_time)
        forecast = select_latest_forecast(
            forecasts_by_start.get(delivery_time, []),
            delivery_time,
            cutoff,
        )
        matches.append(
            {
                "delivery_time": delivery_time,
                "forecast": forecast,
                "cutoff": cutoff,
                "forecast_eligible": forecast is not None,
            }
        )
    return matches


def select_all(
    forecasts: list[NormalizedRecord],
    actuals: list[NormalizedRecord],
    cutoff_func: Callable[[datetime], datetime] = default_cutoff,
) -> list[dict]:
    """Select a forecast for every actual delivery time.

    Kept as a convenience wrapper for callers that already have actuals.
    New orchestration should prefer :func:`select_for_delivery_times` so
    missing actual intervals are represented explicitly.
    """
    actual_by_start = {actual.start_time: actual for actual in actuals}
    matches = select_for_delivery_times(
        forecasts,
        actual_by_start,
        cutoff_func=cutoff_func,
    )
    for match in matches:
        match["actual"] = actual_by_start.get(match["delivery_time"])
    return matches
