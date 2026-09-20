from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare

T = {"start_price": 11, "start_include_km": 3, "per_km": 2.5, "per_slow_min": 0.8, "night_factor": 1.2}

def test_day_short():
    r = calc_fare(5, 2, False, T)
    assert r["total"] == 17.6
    assert r["mileage"] == 5.0
    assert "holiday_factor" not in r

def test_night_long():
    r = calc_fare(18, 12, True, T)
    assert r["total"] == 69.72

def test_compare_delta():
    c = compare_day_night(18, 12, T)
    assert c["night_total"] > c["day_total"]

def test_no_factor_identical_to_before():
    # 不提交日期（None / 缺省）时与改造前完全一致
    assert calc_fare(12.7, 4.5, False, T) == calc_fare(12.7, 4.5, False, T, None)
    assert calc_fare(12.7, 4.5, True, T) == calc_fare(12.7, 4.5, True, T, None)

def test_holiday_day_components():
    # 白天无夜间，直接乘节假日系数，各项四舍五入到分
    r = calc_fare(5, 2, False, T, 1.5)
    assert r["holiday_factor"] == 1.5
    assert r["start"] == 16.5      # 11 * 1.5
    assert r["mileage"] == 7.5     # 5.0 * 1.5
    assert r["slow_fee"] == 2.4    # 1.6 * 1.5
    assert r["total"] == 26.4      # 17.6 * 1.5

def test_holiday_after_night():
    # 命中启用日期时在现行夜间处理之后再乘该系数
    r = calc_fare(18, 12, True, T, 1.5)
    assert r["night_factor"] == 1.2
    assert r["holiday_factor"] == 1.5
    assert r["start"] == 19.8      # 11 * 1.2 * 1.5
    assert r["mileage"] == 67.5    # 37.5 * 1.2 * 1.5
    assert r["slow_fee"] == 17.28  # 9.6 * 1.2 * 1.5
    assert r["total"] == 104.58    # 69.72 * 1.5

def test_holiday_round_to_cent():
    r = calc_fare(5, 2, False, T, 1.05)
    assert r["start"] == 11.55
    assert r["mileage"] == 5.25
    assert r["slow_fee"] == 1.68
    assert r["total"] == 18.48
    for k in ("start", "mileage", "slow_fee", "total"):
        assert round(r[k], 2) == r[k]
