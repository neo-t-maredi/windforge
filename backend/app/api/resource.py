# resource.py
# Wind resource data endpoint — fetches wind speed, Weibull parameters
# and capacity factor estimates from the Global Wind Atlas API
# by site coordinates (lat/lon) and hub height.

from fastapi import APIRouter, HTTPException, Query
from app.services.gwa import fetch_wind_resource

router = APIRouter()

@router.get("/")
async def get_resource(
    lat: float = Query(..., description="Site latitude", ge=-90, le=90),
    lon: float = Query(..., description="Site longitude", ge=-180, le=180),
    height: int = Query(100, description="Hub height in metres", ge=50, le=200)
):
    """
    Fetch wind resource data for a candidate site from Global Wind Atlas.
    Returns mean wind speed, Weibull parameters, and capacity factor.
    """
    try:
        data = await fetch_wind_resource(lat=lat, lon=lon, height=height)
        return data
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))