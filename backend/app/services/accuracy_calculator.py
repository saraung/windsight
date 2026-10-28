"""Pure forecast-accuracy metric calculations.

All functions operate on matched ``(forecast_mw, actual_mw)`` pairs where
both values are present. Missing or invalid values are never coerced to
zero; they are simply excluded from the matched set and counted separately.
"""

from math import sqrt


def calculate_metrics(
    pairs: list[tuple[float, float]],
) -> dict[str, float | int | None]:
    """Calculate MAE, RMSE, bias, and overforecast percentage.

    Parameters
    ----------
    pairs:
        List of ``(forecast_mw, actual_mw)`` tuples for valid matched pairs.

    Returns a dictionary with:

    - ``n``: number of valid matched pairs
    - ``mae``: mean absolute error in MW (forecast − actual), or ``None`` when empty
    - ``rmse``: root mean squared error in MW, or ``None`` when empty
    - ``bias``: mean forecast-minus-actual error in MW; positive means
      overforecasting, negative means underforecasting, or ``None`` when empty
    - ``overforecast_percentage``: proportion of matched intervals where
      forecast exceeds actual, denominator is ``n``, or ``None`` when empty
    """
    n = len(pairs)
    if n == 0:
        return {
            "n": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "overforecast_percentage": None,
        }

    errors = [forecast - actual for forecast, actual in pairs]
    mae = sum(abs(e) for e in errors) / n
    rmse = sqrt(sum(e * e for e in errors) / n)
    bias = sum(errors) / n
    overforecast_percentage = 100.0 * sum(1 for e in errors if e > 0) / n

    return {
        "n": n,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "bias": round(bias, 4),
        "overforecast_percentage": round(overforecast_percentage, 4),
    }
