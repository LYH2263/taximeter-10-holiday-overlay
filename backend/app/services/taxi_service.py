import re
from datetime import date

from app.db import connect
from app.engines.holiday import fare_for_date
from app.engines.night_compare import compare_day_night
from app.repositories import holidays, runs, settings, tariff, trips

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ServiceError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _check_service_date(service_date) -> str:
    text = str(service_date).strip()
    if not _DATE_RE.match(text):
        raise ServiceError(400, f"服务日期格式应为 YYYY-MM-DD：{service_date!r}")
    try:
        date.fromisoformat(text)
    except ValueError:
        raise ServiceError(400, f"服务日期不是有效日期：{text}")
    return text


def _check_factor(factor) -> float:
    try:
        value = float(factor)
    except (TypeError, ValueError):
        raise ServiceError(400, f"系数必须是数字：{factor!r}")
    if value <= 0:
        raise ServiceError(400, f"系数必须大于零：{factor}")
    return value


class TaxiService:
    def __init__(self, conn=None): self._c = conn if conn is not None else connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self): return tariff.get_active(self._c)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def fare(self, distance_km, slow_min, night, trip_id, persist, service_date=None):
        t = tariff.get_active(self._c)
        holiday = None
        if service_date:
            service_date = _check_service_date(service_date)
            holiday = holidays.find_active_by_date(self._c, service_date)
        r = fare_for_date(distance_km, slow_min, night, t, holiday)
        payload = {"distance_km": distance_km, "slow_min": slow_min, "night": night}
        if service_date:
            payload["service_date"] = service_date
        rid = runs.insert(self._c, "fare", payload, r, trip_id) if persist else None
        return {"run_id": rid, **r}
    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}
    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
    def list_holidays(self): return holidays.list_all(self._c)
    def create_holiday(self, service_date, factor):
        service_date = _check_service_date(service_date)
        factor = _check_factor(factor)
        clash = holidays.find_active_by_date(self._c, service_date)
        if clash:
            raise ServiceError(409, f"日期 {service_date} 已存在启用中的记录 #{clash['id']}（系数 {clash['factor']}），与新记录（系数 {factor}）冲突，已拒绝创建")
        return holidays.insert(self._c, service_date, factor)
    def update_holiday(self, holiday_id, service_date=None, factor=None):
        row = holidays.get(self._c, holiday_id)
        if not row:
            raise ServiceError(404, f"节假日系数记录 #{holiday_id} 不存在")
        new_date = row["service_date"] if service_date is None else _check_service_date(service_date)
        new_factor = row["factor"] if factor is None else _check_factor(factor)
        if row["active"]:
            clash = holidays.find_active_by_date(self._c, new_date, exclude_id=holiday_id)
            if clash:
                raise ServiceError(409, f"记录 #{holiday_id} 与记录 #{clash['id']} 同为 {new_date} 且均为启用状态，拒绝同时启用")
        return holidays.update(self._c, holiday_id, new_date, new_factor)
    def set_holiday_active(self, holiday_id, active):
        row = holidays.get(self._c, holiday_id)
        if not row:
            raise ServiceError(404, f"节假日系数记录 #{holiday_id} 不存在")
        if active:
            clash = holidays.find_active_by_date(self._c, row["service_date"], exclude_id=holiday_id)
            if clash:
                raise ServiceError(409, f"记录 #{holiday_id} 与记录 #{clash['id']} 同为 {row['service_date']}，启用将形成两条启用记录，已拒绝")
        return holidays.set_active(self._c, holiday_id, active)
