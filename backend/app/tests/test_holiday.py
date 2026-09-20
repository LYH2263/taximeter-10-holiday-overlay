import sqlite3
import pytest
from app.repositories import holiday


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(holiday.SCHEMA)
    yield c
    c.close()


def test_create_and_lookup(conn):
    row = holiday.create(conn, "2026-01-01", 1.5, "元旦")
    assert row["active"] is True
    assert row["factor"] == 1.5
    hit = holiday.get_active_by_date(conn, "2026-01-01")
    assert hit["id"] == row["id"]
    assert holiday.get_active_by_date(conn, "2026-02-01") is None


def test_duplicate_active_date_rejected_and_named(conn):
    first = holiday.create(conn, "2026-10-01", 2.0, "国庆")
    # 再建一条启用的同日记录：拒绝，并点名已存在那条标识
    with pytest.raises(holiday.HolidayConflict) as ei:
        holiday.create(conn, "2026-10-01", 1.8)
    assert ei.value.existing_id == first["id"]
    # 同日只允许有一条启用
    assert holiday.list_all(conn) and sum(1 for r in holiday.list_all(conn) if r["active"]) == 1


def test_inactive_duplicate_allowed_then_activate_conflict_named(conn):
    first = holiday.create(conn, "2026-10-01", 2.0)
    second = holiday.create(conn, "2026-10-01", 1.5, active=False)  # 停用态可并存
    with pytest.raises(holiday.HolidayConflict) as ei:
        holiday.update(conn, second["id"], active=True)
    # 点名冲突的两条标识
    assert ei.value.existing_id == first["id"]
    assert ei.value.new_id == second["id"]


def test_deactivate_frees_date(conn):
    first = holiday.create(conn, "2026-10-01", 2.0)
    holiday.update(conn, first["id"], active=False)
    assert holiday.get_active_by_date(conn, "2026-10-01") is None
    # 原记录停用后，新记录可启用
    second = holiday.create(conn, "2026-10-01", 3.0)
    assert holiday.get_active_by_date(conn, "2026-10-01")["id"] == second["id"]


def test_update_factor_keeps_active(conn):
    row = holiday.create(conn, "2026-05-01", 1.5)
    updated = holiday.update(conn, row["id"], factor=2.5, note="劳动")
    assert updated["factor"] == 2.5
    assert updated["note"] == "劳动"
    assert updated["active"] is True
