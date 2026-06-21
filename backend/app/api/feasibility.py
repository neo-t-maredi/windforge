# feasibility.py
# Site feasibility assessment endpoint.
# Aggregates wind resource, AEP, LCOE, and CAPEX into a single
# composite feasibility view for a candidate site, plus jurisdictional
# flags for known markets (Netherlands, Saudi Arabia as MVP coverage).

from fastapi import APIRouter, HTTPException, Query, Request
from app.services.gwa import fetch_wind_resource
from app.core.limiter import limiter
from app.services.calculator import (
    air_density,
    air_density_correction_factor,
    calculate_gross_aep,
    apply_losses,
    capacity_factor,
    calculate_lcoe,
)
import math

router = APIRouter()

# MVP jurisdictional data — manually curated for the two markets
# WindForge currently covers. Production version would integrate
# a permitting/grid-queue database per country.
JURISDICTION_FLAGS = {
    "NLD": {
        "permitting_complexity": "Moderate",
        "grid_connection_outlook": "Constrained — TenneT congestion in several "
                                    "provinces, connection queues common",
        "renewable_policy": "Strong — SDE++ subsidy scheme, national 2030 wind targets",
        "typical_timeline_months": "24-36",
    },
    "SAU": {
        "permitting_complexity": "Low-Moderate — centralised under REPDO/NREP",
        "grid_connection_outlook": "Favourable — large-scale grid expansion "
                                    "underway alongside NREP tendering",
        "renewable_policy": "Strong — Vision 2030 target of 50% renewable "
                             "capacity, active utility-scale tendering (NREP Round 7+)",
        "typical_timeline_months": "18-30",
    },
}


@router.get("/")
@limiter.limit("10/minute")
async def get_feasibility(
    request: Request,
    lat: float = Query(..., description="Site latitude", ge=-90, le=90),
    lon: float = Query(..., description="Site longitude", ge=-180, le=180),
    height: int = Query(100, description="Hub height in metres"),
    rated_power_kw: float = Query(4200, description="Turbine rated power in kW"),
    elevation_m: float = Query(0, description="Site elevation above sea level in metres"),
    capex_per_mw_usd: float = Query(1_300_000, description="CAPEX per MW in USD"),
    annual_opex_usd: float = Query(100_000, description="Annual OPEX in USD/year"),
    terrain_complexity: float = Query(1.0, description="Terrain complexity multiplier", ge=1.0, le=2.0),
):
    """
    Run the full feasibility pipeline: wind resource -> AEP -> CAPEX ->
    LCOE -> composite feasibility score with jurisdictional context.
    """
    try:
        resource = await fetch_wind_resource(lat=lat, lon=lon, height=height)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    mean_speed = resource["mean_wind_speed"]
    country = resource["country"]

    weibull_k = 2.0
    weibull_a = mean_speed / math.gamma(1 + 1 / weibull_k)

    site_rho = air_density(elevation_m)
    rho_correction = air_density_correction_factor(site_rho)

    gross_aep_mwh = calculate_gross_aep(
        weibull_k=weibull_k, weibull_a=weibull_a,
        rated_power_kw=rated_power_kw, rho_correction=rho_correction,
    )
    aep_result = apply_losses(gross_aep_mwh)
    net_aep_mwh = aep_result["net_aep_mwh"]
    cf = capacity_factor(net_aep_mwh, rated_power_kw)

    rated_power_mw = rated_power_kw / 1000
    total_capex = rated_power_mw * capex_per_mw_usd * terrain_complexity

    lcoe_result = calculate_lcoe(
        capex=total_capex, annual_opex=annual_opex_usd, net_aep_mwh=net_aep_mwh,
    )

    # Simple composite feasibility scoring — weighted bands on wind
    # resource quality and LCOE competitiveness. MVP heuristic, not
    # a validated investment-grade scoring model.
    score = 0
    if mean_speed >= 7.5:
        score += 40
    elif mean_speed >= 6.0:
        score += 25
    else:
        score += 10

    lcoe = lcoe_result["lcoe_usd_per_mwh"]
    if lcoe <= 35:
        score += 40
    elif lcoe <= 50:
        score += 25
    else:
        score += 10

    if cf >= 0.35:
        score += 20
    elif cf >= 0.25:
        score += 10

    if score >= 80:
        rating = "Strong"
    elif score >= 50:
        rating = "Moderate"
    else:
        rating = "Weak"

    jurisdiction = JURISDICTION_FLAGS.get(country, {
        "permitting_complexity": "Unknown — country not yet covered by WindForge jurisdiction data",
        "grid_connection_outlook": "Unknown",
        "renewable_policy": "Unknown",
        "typical_timeline_months": "Unknown",
    })

    return {
        "site": {"lat": lat, "lon": lon, "country": country},
        "wind_resource": {"mean_wind_speed_ms": mean_speed, "capacity_factor": cf},
        "energy_production": aep_result,
        "financial": {"total_capex_usd": round(total_capex, 2), "lcoe_usd_per_mwh": lcoe},
        "jurisdiction": jurisdiction,
        "feasibility_score": score,
        "feasibility_rating": rating,
        "note": "Composite score is an MVP heuristic for screening purposes only. "
                "Not a substitute for full technical and financial due diligence."
    }