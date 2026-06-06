# lcoe.py
# Levelised Cost of Energy (LCOE) calculation endpoint.
# Parametric inputs: CAPEX, OPEX, discount rate, project lifetime.
# Returns LCOE in USD/MWh against computed AEP.

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_lcoe():
    return {"module": "lcoe", "status": "stub"}