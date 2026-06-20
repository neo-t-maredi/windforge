# lcoe.py
# Levelised Cost of Energy (LCOE) calculation endpoint.
# Pipeline: run the AEP calculation for the site, then apply the
# CRF-based LCOE formula using CAPEX and OPEX inputs.
# Returns LCOE in USD/MWh.

from fastapi import APIRouter, HTTPException, Query
from app.services.gwa import fetch_wind_resource
from app.services.calculator import (
    air_density,
    air_density_correction_factor,
    calculate_gross_aep,
    apply_losses,
    calculate_lcoe,
)
import math

router = APIRouter()


@router.get("/")
async def get_lcoe(
    lat: float = Query(..., description="Site latitude", ge=-90, le=90),
    lon: float = Query(..., description="Site longitude", ge=-180, le=180),
    height: int = Query(100, description="Hub height in metres"),
    rated_power_kw: float = Query(4200, description="Turbine rated power in kW"),
    elevation_m: float = Query(0, description="Site elevation above sea level in metres"),
    temperature_c: float = Query(15.0, description="Site mean annual temperature in Celsius"),
    capex_usd: float = Query(..., description="Total capital expenditure in USD"),
    annual_opex_usd: float = Query(..., description="Annual operating expenditure in USD/year"),
    discount_rate: float = Query(0.07, description="Discount rate as decimal, e.g. 0.07 = 7%"),
    project_lifetime_years: int = Query(20, description="Project lifetime in years"),
):
    """
    Calculate Levelised Cost of Energy for a candidate wind site.
    Runs the full AEP pipeline internally, then applies CRF-based LCOE.
    """
    try:
        resource = await fetch_wind_resource(lat=lat, lon=lon, height=height)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    mean_speed = resource["mean_wind_speed"]
    weibull_k = 2.0
    weibull_a = mean_speed / math.gamma(1 + 1 / weibull_k)

    site_rho = air_density(elevation_m, temperature_c)
    rho_correction = air_density_correction_factor(site_rho)

    gross_aep_mwh = calculate_gross_aep(
        weibull_k=weibull_k,
        weibull_a=weibull_a,
        rated_power_kw=rated_power_kw,
        rho_correction=rho_correction,
    )

    aep_result = apply_losses(gross_aep_mwh)
    net_aep_mwh = aep_result["net_aep_mwh"]

    lcoe_result = calculate_lcoe(
        capex=capex_usd,
        annual_opex=annual_opex_usd,
        net_aep_mwh=net_aep_mwh,
        discount_rate=discount_rate,
        project_lifetime_years=project_lifetime_years,
    )

    return {
        "site": {"lat": lat, "lon": lon, "height": height},
        "energy_production": aep_result,
        "financial_inputs": {
            "capex_usd": capex_usd,
            "annual_opex_usd": annual_opex_usd,
            "discount_rate": discount_rate,
            "project_lifetime_years": project_lifetime_years,
        },
        "lcoe": lcoe_result,
    }

