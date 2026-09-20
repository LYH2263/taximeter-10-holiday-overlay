def calc_fare(distance_km: float, slow_min: float, night: bool, tariff: dict, holiday_factor: float | None = None) -> dict:
    base = float(tariff["start_price"])
    include = float(tariff["start_include_km"])
    per_km = float(tariff["per_km"])
    per_slow = float(tariff["per_slow_min"])
    night_f = float(tariff.get("night_factor", 1.0)) if night else 1.0
    # 节假日系数在现行夜间处理之后再乘；不提交/不命中时为 None，结果与改造前完全一致
    hol_f = float(holiday_factor) if holiday_factor is not None else 1.0
    dist = max(0.0, float(distance_km) - include)
    mile = dist * per_km
    slow = float(slow_min) * per_slow
    sub = base + mile + slow
    r = {
        "distance_km": round(float(distance_km), 2),
        "slow_min": round(float(slow_min), 1),
        "night": night,
        "night_factor": night_f,
        "start": round(base * night_f * hol_f, 2),
        "mileage": round(mile * night_f * hol_f, 2),
        "slow_fee": round(slow * night_f * hol_f, 2),
        "total": round(sub * night_f * hol_f, 2),
    }
    if holiday_factor is not None:
        r["holiday_factor"] = hol_f
    return r
