from fastapi import APIRouter
from app.routers import dashboard, fare, history, holiday, settings, tariff, trips

api = APIRouter(prefix="/api")
for r in (dashboard, trips, tariff, holiday, fare, history, settings):
    api.include_router(r.router)
