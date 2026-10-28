"""Pure forecast-accuracy metric calculations.

All functions operate on matched ``(forecast_mw, actual_mw)`` pairs where
both values are present. Missing or invalid values are never coerced to
zero; they are simply excluded from the matched set and counted separately.
"""

from collections import defaultdict
from datetime import date
from math import sqrt


def _percentile(sorted_values: list[float], fraction: float) -> float:
    """Linear-interpolation percentile for a non-empty sorted list."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def calculate_metrics(
    pairs: list[tuple[float, float]],
) -> dict[str, float | int | None]:
    """Calculate MAE, RMSE, bias, error quantiles, and forecast direction.

    Parameters
    ----------
    pairs:
        List of ``(forecast_mw, actual_mw)`` tuples for valid matched pairs.

    Returns a dictionary with:

    - ``n``: number of valid matched pairs
    - ``mae``: mean absolute error in MW (forecast - actual), or ``None`` when empty
    - ``rmse``: root mean squared error in MW, or ``None`` when empty
    - ``bias``: mean forecast-minus-actual error in MW; positive means
      overforecasting, negative means underforecasting, or ``None`` when empty
    - ``overforecast_percentage``: proportion of matched intervals where
      forecast exceeds actual, denominator is ``n``, or ``None`` when empty
    - ``underforecast_percentage``: proportion where forecast is below actual
    - ``error_p10``, ``error_p50``, ``error_p90``: error quantiles in MW
    """
    n = len(pairs)
    if n == 0:
        return {
            "n": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "overforecast_percentage": None,
            "underforecast_percentage": None,
            "error_p10": None,
            "error_p50": None,
            "error_p90": None,
        }

    errors = [forecast - actual for forecast, actual in pairs]
    sorted_errors = sorted(errors)
    mae = sum(abs(error) for error in errors) / n
    rmse = sqrt(sum(error * error for error in errors) / n)
    bias = sum(errors) / n
    overforecast_percentage = 100.0 * sum(1 for error in errors if error > 0) / n
    underforecast_percentage = 100.0 * sum(1 for error in errors if error < 0) / n

    return {
        "n": n,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "bias": round(bias, 4),
        "overforecast_percentage": round(overforecast_percentage, 4),
        "underforecast_percentage": round(underforecast_percentage, 4),
        "error_p10": round(_percentile(sorted_errors, 0.10), 4),
        "error_p50": round(_percentile(sorted_errors, 0.50), 4),
        "error_p90": round(_percentile(sorted_errors, 0.90), 4),
    }


def calculate_daily_metrics(
    dated_pairs: list[tuple[date, float, float]],
) -> list[dict[str, object]]:
    """Calculate one metrics row per UTC delivery date."""
    grouped: dict[date, list[tuple[float, float]]] = defaultdict(list)
    for delivery_date, forecast_mw, actual_mw in dated_pairs:
        grouped[delivery_date].append((forecast_mw, actual_mw))

    return [
        {"date": delivery_date, **calculate_metrics(pairs)}
        for delivery_date, pairs in sorted(grouped.items())
    ]
