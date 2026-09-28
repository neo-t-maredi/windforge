# lcoe.py
# Levelised Cost of Energy (LCOE) calculation endpoint.
# Pipeline: run the AEP calculation for the site, then apply the
# CRF-based LCOE formula using CAPEX and OPEX inputs.
# Returns LCOE in USD/MWh.

from fastapi import APIRouter, HTTPException, Query
from app.services.gwa import fetch_wind_resource, ResourceUnavailable
from app.services.calculator import (
    validate_curve,
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
    rated_power_kw: float = Query(4200, gt=0, le=1000000, description="Turbine rated power in kW"),
    cut_in: float = Query(3., ge=0, le=100),
    rated_speed: float = Query(12., gt=0, le=100),
    cut_out: float = Query(25., gt=0, le=100),
    elevation_m: float = Query(0, ge=-500, le=11000, description="Site elevation above sea level in metres"),
    temperature_c: float = Query(15.0, ge=-100, le=100, description="Site mean annual temperature in Celsius"),
    capex_usd: float | None = Query(None, ge=0, le=1e15, description="Total capital expenditure in USD"),
    capex_per_mw_usd: float = Query(1300000, gt=0, le=1e12),
    terrain_complexity: float = Query(1., ge=1, le=2),
    annual_opex_usd: float = Query(100000, ge=0, le=1e15, description="Annual operating expenditure in USD/year"),
    discount_rate: float = Query(0.07, ge=0, le=1, description="Discount rate as decimal, e.g. 0.07 = 7%"),
    project_lifetime_years: int = Query(20, ge=1, le=100, description="Project lifetime in years"),
):
    """
    Calculate Levelised Cost of Energy for a candidate wind site.
    Runs the full AEP pipeline internally, then applies CRF-based LCOE.
    """
    if height not in (50, 100, 200):
        raise HTTPException(422, "Height must be 50, 100 or 200 m")
    try:
        validate_curve(rated_power_kw, cut_in, rated_speed, cut_out)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    try:
        resource = await fetch_wind_resource(lat=lat, lon=lon, height=height)
    except ValueError as e:
        raise HTTPException(status_code=502 if isinstance(e, ResourceUnavailable) else 422, detail=str(e)) from e

    mean_speed = resource["mean_wind_speed"]
    weibull_k = 2.0
    weibull_a = mean_speed / math.gamma(1 + 1 / weibull_k)

    site_rho = air_density(elevation_m, temperature_c)
    rho_correction = air_density_correction_factor(site_rho)

    gross_aep_mwh = calculate_gross_aep(
        cut_in=cut_in, rated_speed=rated_speed, cut_out=cut_out,
        weibull_k=weibull_k,
        weibull_a=weibull_a,
        rated_power_kw=rated_power_kw,
        rho_correction=rho_correction,
    )

    aep_result = apply_losses(gross_aep_mwh)
    net_aep_mwh = aep_result["net_aep_mwh"]

    if capex_usd is None:
        capex_usd = rated_power_kw / 1000 * capex_per_mw_usd * terrain_complexity
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

