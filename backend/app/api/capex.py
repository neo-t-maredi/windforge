# capex.py
# Capital expenditure modelling endpoint.
# Breaks down total CAPEX into standard onshore wind project cost
# categories: turbine supply, balance of plant (BOP), grid connection,
# and soft costs (development, engineering, contingency).
# Industry-typical cost ratios used as defaults — these are planning
# estimates, not bankable quotes.

from fastapi import APIRouter, Query

router = APIRouter()

# Typical onshore wind CAPEX breakdown as fraction of total turbine cost
# Source: NREL Cost of Wind Energy Review, IRENA onshore wind cost reports
DEFAULT_COST_RATIOS = {
    "turbine_supply": 0.65,      # turbine, tower, nacelle, blades, transport
    "balance_of_plant": 0.20,    # foundations, roads, civil works, cabling
    "grid_connection": 0.08,     # substation, transformer, transmission line
    "soft_costs": 0.07,          # development, engineering, permitting, contingency
}

# Typical CAPEX per MW for onshore wind (USD/MW) — used as a default
# planning estimate when the user doesn't supply a known turbine price
DEFAULT_CAPEX_PER_MW_USD = 1_300_000


@router.get("/")
def get_capex(
    rated_power_kw: float = Query(4200, description="Turbine rated power in kW"),
    capex_per_mw_usd: float = Query(
        DEFAULT_CAPEX_PER_MW_USD,
        description="CAPEX per MW in USD. Defaults to industry-typical onshore estimate."
    ),
    terrain_complexity: float = Query(
        1.0,
        description="Terrain complexity multiplier (1.0 = flat/easy access, "
                     "1.15-1.3 = hilly/ridge sites, 1.3-1.5 = mountainous/remote)",
        ge=1.0,
        le=2.0,
    ),
):
    """
    Estimate total CAPEX and cost category breakdown for a candidate site.
    Terrain complexity multiplier accounts for the fact that the same
    turbine costs significantly more to install on difficult terrain
    due to civil works, road access, and crane logistics.
    """
    rated_power_mw = rated_power_kw / 1000

    base_capex = rated_power_mw * capex_per_mw_usd
    total_capex = base_capex * terrain_complexity

    breakdown = {
        category: round(total_capex * ratio, 2)
        for category, ratio in DEFAULT_COST_RATIOS.items()
    }

    return {
        "turbine": {
            "rated_power_kw": rated_power_kw,
            "rated_power_mw": rated_power_mw,
        },
        "capex_assumptions": {
            "capex_per_mw_usd": capex_per_mw_usd,
            "terrain_complexity_multiplier": terrain_complexity,
            "note": "Planning-level estimate based on NREL/IRENA typical onshore "
                    "wind cost ratios. Not a bankable quote — actual CAPEX requires "
                    "EPC tendering and site-specific civil engineering assessment."
        },
        "total_capex_usd": round(total_capex, 2),
        "cost_breakdown_usd": breakdown,
        "cost_breakdown_pct": DEFAULT_COST_RATIOS,
    }