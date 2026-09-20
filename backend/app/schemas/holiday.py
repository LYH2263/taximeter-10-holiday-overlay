from pydantic import BaseModel

class HolidayCreate(BaseModel):
    service_date: str
    factor: float

class HolidayUpdate(BaseModel):
    service_date: str | None = None
    factor: float | None = None
