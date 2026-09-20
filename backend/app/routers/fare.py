from fastapi import APIRouter, HTTPException
from app.schemas.fare import CompareRequest, FareRequest
from app.services.taxi_service import ServiceError, TaxiService
router = APIRouter()
@router.post("/fare")
def post_fare(body: FareRequest):
    try:
        with TaxiService() as s:
            return s.fare(body.distance_km, body.slow_min, body.night, body.trip_id, body.persist, body.service_date)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.message)
@router.post("/compare")
def post_compare(body: CompareRequest):
    with TaxiService() as s:
        return s.compare(body.distance_km, body.slow_min, body.persist)
