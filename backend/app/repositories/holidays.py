import sqlite3
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM holiday_factors ORDER BY service_date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


def get(conn: sqlite3.Connection, holiday_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM holiday_factors WHERE id=?", (holiday_id,)).fetchone()
    return dict(row) if row else None


def find_active_by_date(conn: sqlite3.Connection, service_date: str, exclude_id: int | None = None) -> dict | None:
    sql = "SELECT * FROM holiday_factors WHERE service_date=? AND active=1"
    params: list = [service_date]
    if exclude_id is not None:
        sql += " AND id<>?"
        params.append(exclude_id)
    row = conn.execute(sql + " ORDER BY id LIMIT 1", params).fetchone()
    return dict(row) if row else None


def insert(conn: sqlite3.Connection, service_date: str, factor: float) -> dict:
    now = _now()
    cur = conn.execute(
        "INSERT INTO holiday_factors(service_date,factor,active,created_at,updated_at) VALUES (?,?,1,?,?)",
        (service_date, float(factor), now, now),
    )
    conn.commit()
    return get(conn, int(cur.lastrowid))


def update(conn: sqlite3.Connection, holiday_id: int, service_date: str, factor: float) -> dict:
    conn.execute(
        "UPDATE holiday_factors SET service_date=?, factor=?, updated_at=? WHERE id=?",
        (service_date, float(factor), _now(), holiday_id),
    )
    conn.commit()
    return get(conn, holiday_id)


def set_active(conn: sqlite3.Connection, holiday_id: int, active: bool) -> dict:
    conn.execute(
        "UPDATE holiday_factors SET active=?, updated_at=? WHERE id=?",
        (1 if active else 0, _now(), holiday_id),
    )
    conn.commit()
    return get(conn, holiday_id)
