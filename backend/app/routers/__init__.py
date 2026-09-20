from fastapi import APIRouter
from app.routers import dashboard, fare, history, holidays, settings, tariff, trips

api = APIRouter(prefix="/api")
for r in (dashboard, trips, tariff, fare, history, settings, holidays):
    api.include_router(r.router)
