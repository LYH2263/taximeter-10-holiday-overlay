import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS holiday_factors(
    id INTEGER PRIMARY KEY,
    service_date TEXT NOT NULL,
    factor REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_holiday_active_date
    ON holiday_factors(service_date) WHERE active = 1;
"""


class HolidayConflict(Exception):
    """同一服务日期已有另一条启用记录。existing/new 为两条记录的标识。"""

    def __init__(self, service_date: str, existing_id: int, new_id: int | None = None):
        self.service_date = service_date
        self.existing_id = existing_id
        self.new_id = new_id
        super().__init__(
            f"服务日期 {service_date} 已有启用系数（#{existing_id}），"
            + (f"与本次记录（#{new_id}）冲突" if new_id is not None else "不可重复启用")
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_factor(factor: float) -> float:
    f = float(factor)
    if not (f > 0):
        raise ValueError("节假日系数必须大于零")
    return f


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["active"] = bool(d["active"])
    d["factor"] = float(d["factor"])
    return d


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM holiday_factors ORDER BY service_date, id"
    ).fetchall()
    return [_row(r) for r in rows]


def get(conn: sqlite3.Connection, holiday_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM holiday_factors WHERE id=?", (holiday_id,)
    ).fetchone()
    return _row(row) if row else None


def get_active_by_date(conn: sqlite3.Connection, service_date: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM holiday_factors WHERE service_date=? AND active=1 ORDER BY id LIMIT 1",
        (service_date,),
    ).fetchone()
    return _row(row) if row else None


def create(conn: sqlite3.Connection, service_date: str, factor: float, note: str | None = None, active: bool = True) -> dict:
    factor = _check_factor(factor)
    if active:
        other = get_active_by_date(conn, service_date)
        if other is not None:
            raise HolidayConflict(service_date, other["id"])
    now = _now()
    cur = conn.execute(
        "INSERT INTO holiday_factors(service_date,factor,active,note,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        (service_date, float(factor), 1 if active else 0, note, now, now),
    )
    conn.commit()
    return get(conn, int(cur.lastrowid))


def update(
    conn: sqlite3.Connection,
    holiday_id: int,
    factor: float | None = None,
    note: str | None = None,
    active: bool | None = None,
) -> dict | None:
    row = get(conn, holiday_id)
    if row is None:
        return None
    new_factor = row["factor"] if factor is None else _check_factor(factor)
    new_note = row["note"] if note is None else note
    new_active = row["active"] if active is None else bool(active)
    # 仅在“最终为启用”时校验同日是否存在另一条启用记录；停用自身不触发
    if new_active:
        other = conn.execute(
            "SELECT id FROM holiday_factors WHERE service_date=? AND active=1 AND id<>?",
            (row["service_date"], holiday_id),
        ).fetchone()
        if other is not None:
            raise HolidayConflict(row["service_date"], int(other["id"]), holiday_id)
    conn.execute(
        "UPDATE holiday_factors SET factor=?, note=?, active=?, updated_at=? WHERE id=?",
        (new_factor, new_note, 1 if new_active else 0, _now(), holiday_id),
    )
    conn.commit()
    return get(conn, holiday_id)
