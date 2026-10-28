"""Pure forecast-vintage selection logic.

Selects, for each delivery interval, the latest forecast that had been
published at or before a chosen decision cutoff. No look-ahead bias: a
forecast published *after* the cutoff is never eligible, regardless of how
much more accurate it might be.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.schemas.records import NormalizedRecord


def default_cutoff(delivery_time: datetime) -> datetime:
    """Default decision cutoff: D-1 12:00 UTC.

    For a delivery at ``delivery_time``, the cutoff is noon UTC on the
    calendar day before the delivery date. This is a sensible day-ahead
    procurement assumption; it is configurable and must be made visible to
    the user.
    """
    delivery_date = delivery_time.astimezone(timezone.utc).date()
    cutoff_date = delivery_date - timedelta(days=1)
    return datetime(
        cutoff_date.year,
        cutoff_date.month,
        cutoff_date.day,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )


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

    def sort_key(f: NormalizedRecord) -> tuple[datetime, float, int]:
        # generation_mw None sorts lowest; index breaks remaining ties deterministically
        gen = f.generation_mw if f.generation_mw is not None else float("-inf")
        return (f.publish_time, gen)

    eligible.sort(key=sort_key, reverse=True)
    return eligible[0]


def select_all(
    forecasts: list[NormalizedRecord],
    actuals: list[NormalizedRecord],
    cutoff_func: Callable[[datetime], datetime] = default_cutoff,
) -> list[dict]:
    """Select a forecast for every actual delivery time.

    Returns a list of match dictionaries with keys:

    - ``delivery_time``: the delivery interval start (UTC)
    - ``actual``: the matched :class:`NormalizedRecord` or ``None``
    - ``forecast``: the selected :class:`NormalizedRecord` or ``None``
    - ``cutoff``: the decision cutoff applied for this interval
    - ``forecast_eligible``: whether at least one forecast passed the cutoff
    """
    forecasts_by_start: dict[datetime, list[NormalizedRecord]] = defaultdict(list)
    for f in forecasts:
        forecasts_by_start[f.start_time].append(f)

    matches: list[dict] = []
    for actual in actuals:
        cutoff = cutoff_func(actual.start_time)
        forecast = select_latest_forecast(
            forecasts_by_start.get(actual.start_time, []),
            actual.start_time,
            cutoff,
        )
        matches.append(
            {
                "delivery_time": actual.start_time,
                "actual": actual,
                "forecast": forecast,
                "cutoff": cutoff,
                "forecast_eligible": forecast is not None,
            }
        )
    return matches
