from fastapi import APIRouter, HTTPException
from app.repositories.holiday import HolidayConflict
from app.schemas.holiday import HolidayCreate, HolidayUpdate
from app.services.taxi_service import TaxiService
router = APIRouter()

@router.get("/holidays")
def list_holidays():
    with TaxiService() as s:
        return {"items": s.list_holidays()}

@router.post("/holidays")
def create_holiday(body: HolidayCreate):
    with TaxiService() as s:
        try:
            return s.create_holiday(body.service_date.isoformat(), body.factor, body.note, body.active)
        except HolidayConflict as e:
            raise HTTPException(
                status_code=409,
                detail=f"服务日期 {e.service_date} 已存在启用记录 #{e.existing_id}，本次新增被拒绝；请先停用 # {e.existing_id}。",
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

@router.patch("/holidays/{holiday_id}")
def update_holiday(holiday_id: int, body: HolidayUpdate):
    with TaxiService() as s:
        try:
            row = s.update_holiday(holiday_id, body.factor, body.note, body.active)
        except HolidayConflict as e:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"服务日期 {e.service_date} 同时存在两条启用记录："
                    f"#{e.existing_id} 与 #{e.new_id}，拒绝启用 #{e.new_id}；请先停用其中一条。"
                ),
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if row is None:
            raise HTTPException(status_code=404, detail="节假日系数记录不存在")
        return row
