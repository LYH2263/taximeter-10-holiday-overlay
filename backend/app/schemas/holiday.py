from datetime import date
from pydantic import BaseModel, Field

class HolidayCreate(BaseModel):
    service_date: date
    factor: float = Field(gt=0)
    note: str | None = None
    active: bool = True

class HolidayUpdate(BaseModel):
    factor: float | None = Field(default=None, gt=0)
    note: str | None = None
    active: bool | None = None
