# aep.py
# Annual Energy Production (AEP) calculation endpoint.
# Computes energy yield from Weibull wind distribution and turbine
# power curve following IEC 61400-12-1 methodology.

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_aep():
    return {"module": "aep", "status": "stub"}