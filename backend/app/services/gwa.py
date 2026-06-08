# gwa.py
# Global Wind Atlas API service layer.
# Fetches wind resource data by coordinates (lat/lon) and hub height.
# GWA exposes separate endpoints per variable — meanwindspeed, weibull k/A,
# and capacity factor. We call them individually and aggregate.

import httpx

GWA_BASE = "https://globalwindatlas.info/api/gwa/custom"

VALID_HEIGHTS = [10, 50, 100, 150, 200]

async def fetch_wind_resource(lat: float, lon: float, height: int = 100) -> dict:
    """
    Fetch wind resource data from Global Wind Atlas for a given location.
    Calls three endpoints: meanwindspeed, weibull parameters, capacity factor.
    """
    if height not in VALID_HEIGHTS:
        raise ValueError(f"Height must be one of {VALID_HEIGHTS}m")

    results = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Mean wind speed
        for variable in ["meanwindspeed", "weibull-A", "weibull-k", "capacity-factor_IEC1"]:
            url = f"{GWA_BASE}/{variable}"
            params = {"lat": lat, "lon": lon, "height": height}

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                results[variable] = response.json()
            except httpx.HTTPStatusError as e:
                raise ValueError(f"GWA API error [{variable}]: {e.response.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"GWA connection error: {str(e)}")

    return {
        "lat": lat,
        "lon": lon,
        "height": height,
        "mean_wind_speed": results.get("meanwindspeed"),
        "weibull_a": results.get("weibull-A"),
        "weibull_k": results.get("weibull-k"),
        "capacity_factor": results.get("capacity-factor_IEC1"),
        "source": "Global Wind Atlas v3"
    }