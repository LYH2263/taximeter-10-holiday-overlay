from fastapi import APIRouter, HTTPException
from app.schemas.holiday import HolidayCreate, HolidayUpdate
from app.services.taxi_service import ServiceError, TaxiService

router = APIRouter()


def _guard(fn):
    try:
        return fn()
    except ServiceError as e:
        raise HTTPException(e.status_code, e.message)


@router.get("/holidays")
def list_holidays():
    with TaxiService() as s:
        return {"items": s.list_holidays()}


@router.post("/holidays", status_code=201)
def create_holiday(body: HolidayCreate):
    with TaxiService() as s:
        return _guard(lambda: s.create_holiday(body.service_date, body.factor))


@router.put("/holidays/{holiday_id}")
def update_holiday(holiday_id: int, body: HolidayUpdate):
    with TaxiService() as s:
        return _guard(lambda: s.update_holiday(holiday_id, body.service_date, body.factor))


@router.post("/holidays/{holiday_id}/deactivate")
def deactivate_holiday(holiday_id: int):
    with TaxiService() as s:
        return _guard(lambda: s.set_holiday_active(holiday_id, False))


@router.post("/holidays/{holiday_id}/activate")
def activate_holiday(holiday_id: int):
    with TaxiService() as s:
        return _guard(lambda: s.set_holiday_active(holiday_id, True))
