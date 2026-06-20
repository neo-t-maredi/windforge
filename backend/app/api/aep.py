# aep.py
# Annual Energy Production (AEP) calculation endpoint.
# Pipeline: fetch wind resource from GWA -> calculate Weibull-integrated
# gross AEP -> apply air density correction -> apply parametric losses
# -> return net AEP following IEC 61400-12-1 aligned methodology.

from fastapi import APIRouter, HTTPException, Query
from app.services.gwa import fetch_wind_resource
from app.services.calculator import (
    air_density,
    air_density_correction_factor,
    calculate_gross_aep,
    apply_losses,
    capacity_factor,
)
import math

router = APIRouter()


@router.get("/")
async def get_aep(
    lat: float = Query(..., description="Site latitude", ge=-90, le=90),
    lon: float = Query(..., description="Site longitude", ge=-180, le=180),
    height: int = Query(100, description="Hub height in metres"),
    rated_power_kw: float = Query(4200, description="Turbine rated power in kW"),
    elevation_m: float = Query(0, description="Site elevation above sea level in metres"),
    temperature_c: float = Query(15.0, description="Site mean annual temperature in Celsius"),
    cut_in: float = Query(3.0, description="Turbine cut-in wind speed (m/s)"),
    rated_speed: float = Query(12.0, description="Turbine rated wind speed (m/s)"),
    cut_out: float = Query(25.0, description="Turbine cut-out wind speed (m/s)"),
):
    """
    Calculate Annual Energy Production for a candidate site.

    Note: GWA provides mean wind speed but not Weibull k/A shape parameters
    via the simple raster endpoint used here. As an MVP approximation, we
    derive a representative Weibull shape (k=2.0, typical for onshore sites)
    scaled to match the GWA mean wind speed. This is flagged in the response
    as an approximation pending full Weibull parameter raster integration.
    """
    try:
        resource = await fetch_wind_resource(lat=lat, lon=lon, height=height)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    mean_speed = resource["mean_wind_speed"]

    # MVP approximation: assume k=2.0 (Rayleigh distribution, common onshore default)
    # and derive scale parameter A from mean speed using the Weibull mean formula:
    # mean = A * Gamma(1 + 1/k)
    
    weibull_k = 2.0
    weibull_a = mean_speed / math.gamma(1 + 1 / weibull_k)

    site_rho = air_density(elevation_m, temperature_c)
    rho_correction = air_density_correction_factor(site_rho)

    gross_aep_mwh = calculate_gross_aep(
        weibull_k=weibull_k,
        weibull_a=weibull_a,
        rated_power_kw=rated_power_kw,
        rho_correction=rho_correction,
        cut_in=cut_in,
        rated_speed=rated_speed,
        cut_out=cut_out,
    )

    aep_result = apply_losses(gross_aep_mwh)
    cf = capacity_factor(aep_result["net_aep_mwh"], rated_power_kw)

    return {
        "site": {"lat": lat, "lon": lon, "height": height},
        "wind_resource": {
            "mean_wind_speed_ms": mean_speed,
            "weibull_k_assumed": weibull_k,
            "weibull_a_derived": round(weibull_a, 3),
            "note": "Weibull k assumed at 2.0 (Rayleigh approximation) — full GWA "
                    "shape/scale raster integration planned for production version"
        },
        "site_conditions": {
            "elevation_m": elevation_m,
            "temperature_c": temperature_c,
            "air_density_kg_m3": site_rho,
            "air_density_correction_factor": round(rho_correction, 4),
        },
        "turbine": {
            "rated_power_kw": rated_power_kw,
            "cut_in_ms": cut_in,
            "rated_speed_ms": rated_speed,
            "cut_out_ms": cut_out,
        },
        "energy_production": aep_result,
        "capacity_factor": cf,
    }