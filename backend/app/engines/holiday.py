from decimal import ROUND_HALF_UP, Decimal

from app.engines.tariff_breakdown import calc_fare

_CENT = Decimal("0.01")
_SCALED_KEYS = ("start", "mileage", "slow_fee", "total")


def _times_factor(value: float, factor: float) -> float:
    product = Decimal(str(value)) * Decimal(str(factor))
    return float(product.quantize(_CENT, rounding=ROUND_HALF_UP))


def apply_holiday(breakdown: dict, holiday: dict) -> dict:
    """Multiply a night-processed breakdown by the holiday factor.

    start/mileage/slow_fee/total are each rounded half-up to cents after
    multiplication; pre-holiday numbers are kept under "pre_holiday".
    """
    factor = float(holiday["factor"])
    out = dict(breakdown)
    out["pre_holiday"] = {k: breakdown[k] for k in _SCALED_KEYS}
    for key in _SCALED_KEYS:
        out[key] = _times_factor(breakdown[key], factor)
    out["holiday"] = {"id": holiday["id"], "service_date": holiday["service_date"], "factor": factor}
    return out


def fare_for_date(distance_km: float, slow_min: float, night: bool, tariff: dict, holiday: dict | None = None) -> dict:
    """Fare for a service date: night processing first, holiday factor after.

    With no holiday hit the result is byte-identical to calc_fare plus a
    null "holiday" marker.
    """
    base = calc_fare(distance_km, slow_min, night, tariff)
    if not holiday:
        base["holiday"] = None
        return base
    return apply_holiday(base, holiday)
