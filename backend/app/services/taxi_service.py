from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.repositories import holiday, runs, settings, tariff, trips

class TaxiService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self): return tariff.get_active(self._c)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def list_holidays(self): return holiday.list_all(self._c)
    def create_holiday(self, service_date, factor, note=None, active=True):
        return holiday.create(self._c, service_date, factor, note, active)
    def update_holiday(self, holiday_id, factor=None, note=None, active=None):
        return holiday.update(self._c, holiday_id, factor, note, active)
    def fare(self, distance_km, slow_min, night, trip_id, persist, service_date=None):
        t = tariff.get_active(self._c)
        date_str = service_date.isoformat() if service_date is not None else None
        hol = holiday.get_active_by_date(self._c, date_str) if date_str else None
        holiday_factor = hol["factor"] if hol else None
        r = calc_fare(distance_km, slow_min, night, t, holiday_factor)
        if date_str:
            r["service_date"] = date_str
        if hol:
            r["holiday_id"] = hol["id"]
        if persist:
            payload = {"distance_km": distance_km, "slow_min": slow_min, "night": night}
            if date_str:
                payload["service_date"] = date_str
            rid = runs.insert(self._c, "fare", payload, r, trip_id)
        else:
            rid = None
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
