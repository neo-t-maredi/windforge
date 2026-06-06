# resource.py
# Wind resource data endpoint — fetches wind speed, Weibull parameters
# and capacity factor estimates from the Global Wind Atlas API
# by site coordinates (lat/lon) and hub height.

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_resource():
    return {"module": "wind resource", "status": "stub"}