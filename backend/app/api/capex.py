# capex.py
# Capital expenditure modelling endpoint.
# Breaks down turbine, civil, grid connection, and balance
# of plant costs by installed capacity (MW).

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_capex():
    return {"module": "capex", "status": "stub"}