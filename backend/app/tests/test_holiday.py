import json
import sqlite3

import pytest

from app.engines.holiday import apply_holiday, fare_for_date
from app.engines.tariff_breakdown import calc_fare
from app.services.taxi_service import ServiceError, TaxiService

T = {"start_price": 11, "start_include_km": 3, "per_km": 2.5, "per_slow_min": 0.8, "night_factor": 1.2}

SCHEMA = """
CREATE TABLE tariff(id INTEGER PRIMARY KEY, start_price REAL, start_include_km REAL, per_km REAL, per_slow_min REAL, night_factor REAL);
CREATE TABLE calc_runs(id INTEGER PRIMARY KEY, kind TEXT, trip_id INTEGER, input_json TEXT, result_json TEXT, created_at TEXT);
CREATE TABLE holiday_factors(id INTEGER PRIMARY KEY, service_date TEXT NOT NULL, factor REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT, updated_at TEXT);
"""


def make_service() -> TaxiService:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO tariff(start_price,start_include_km,per_km,per_slow_min,night_factor) VALUES (?,?,?,?,?)",
        (T["start_price"], T["start_include_km"], T["per_km"], T["per_slow_min"], T["night_factor"]),
    )
    conn.commit()
    return TaxiService(conn)


def test_apply_holiday_scales_and_rounds_half_up():
    breakdown = {"start": 10.05, "mileage": 5.0, "slow_fee": 1.6, "total": 16.65}
    out = apply_holiday(breakdown, {"id": 7, "service_date": "2026-10-01", "factor": 1.5})
    assert out["start"] == 15.08  # 15.075 -> half-up, not banker's 15.07
    assert out["mileage"] == 7.5
    assert out["slow_fee"] == 2.4
    assert out["total"] == 24.98  # 24.975 -> 24.98
    assert out["pre_holiday"] == breakdown
    assert out["holiday"] == {"id": 7, "service_date": "2026-10-01", "factor": 1.5}


def test_fare_for_date_without_holiday_matches_legacy():
    legacy = calc_fare(18, 12, True, T)
    r = fare_for_date(18, 12, True, T, None)
    assert r["holiday"] is None
    for key in ("start", "mileage", "slow_fee", "total", "night_factor"):
        assert r[key] == legacy[key]


def test_fare_for_date_with_holiday_multiplies_after_night():
    holiday = {"id": 1, "service_date": "2026-10-01", "factor": 1.5}
    r = fare_for_date(18, 12, True, T, holiday)
    # night first: start 13.2, mileage 45.0, slow 11.52, total 69.72; then x1.5
    assert r["start"] == 19.8
    assert r["mileage"] == 67.5
    assert r["slow_fee"] == 17.28
    assert r["total"] == 104.58
    assert r["pre_holiday"]["total"] == 69.72


def test_create_holiday_and_conflict_names_both():
    s = make_service()
    first = s.create_holiday("2026-10-01", 1.5)
    assert first["active"] == 1
    with pytest.raises(ServiceError) as e:
        s.create_holiday("2026-10-01", 2.0)
    assert e.value.status_code == 409
    assert f"#{first['id']}" in e.value.message
    assert "2.0" in e.value.message  # incoming record identified too


def test_factor_must_be_positive():
    s = make_service()
    for bad in (0, -1.5):
        with pytest.raises(ServiceError) as e:
            s.create_holiday("2026-10-02", bad)
        assert e.value.status_code == 400
        assert "大于零" in e.value.message
    row = s.create_holiday("2026-10-02", 1.2)
    with pytest.raises(ServiceError):
        s.update_holiday(row["id"], factor=0)


def test_invalid_service_date_rejected():
    s = make_service()
    for bad in ("2026-13-01", "10/01/2026", "2026-1-1"):
        with pytest.raises(ServiceError) as e:
            s.create_holiday(bad, 1.5)
        assert e.value.status_code == 400


def test_deactivate_allows_new_entry_and_activate_conflict_names_both():
    s = make_service()
    a = s.create_holiday("2026-10-01", 1.5)
    s.set_holiday_active(a["id"], False)
    b = s.create_holiday("2026-10-01", 1.3)
    assert b["active"] == 1
    with pytest.raises(ServiceError) as e:
        s.set_holiday_active(a["id"], True)
    assert e.value.status_code == 409
    assert f"#{a['id']}" in e.value.message and f"#{b['id']}" in e.value.message


def test_update_to_colliding_date_names_both():
    s = make_service()
    a = s.create_holiday("2026-10-01", 1.5)
    b = s.create_holiday("2026-10-02", 1.3)
    with pytest.raises(ServiceError) as e:
        s.update_holiday(b["id"], service_date="2026-10-01")
    assert e.value.status_code == 409
    assert f"#{a['id']}" in e.value.message and f"#{b['id']}" in e.value.message
    # factor-only update on an active row is fine
    assert s.update_holiday(b["id"], factor=1.4)["factor"] == 1.4


def test_fare_with_hit_persists_snapshot_immune_to_later_change():
    s = make_service()
    h = s.create_holiday("2026-10-01", 1.5)
    r = s.fare(18, 12, True, None, True, "2026-10-01")
    assert r["total"] == 104.58
    assert r["holiday"]["factor"] == 1.5
    run_id = r["run_id"]
    s.update_holiday(h["id"], factor=3.0)
    stored = [x for x in s.history() if x["id"] == run_id][0]
    result = json.loads(stored["result_json"])
    assert result["total"] == 104.58
    assert result["holiday"]["factor"] == 1.5
    assert json.loads(stored["input_json"])["service_date"] == "2026-10-01"


def test_fare_without_date_or_miss_matches_legacy_and_trial_writes_nothing():
    s = make_service()
    s.create_holiday("2026-10-01", 1.5)
    legacy = calc_fare(5, 2, False, T)
    no_date = s.fare(5, 2, False, None, False, None)
    miss = s.fare(5, 2, False, None, False, "2026-10-02")
    for r in (no_date, miss):
        assert r["holiday"] is None
        assert r["total"] == legacy["total"]
        assert r["start"] == legacy["start"]
        assert r["slow_fee"] == legacy["slow_fee"]
    assert s.history() == []  # persist=False -> read-only trial
