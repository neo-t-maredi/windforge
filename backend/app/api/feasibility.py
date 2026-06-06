# feasibility.py
# Site feasibility assessment endpoint.
# Aggregates AEP, LCOE, CAPEX, and jurisdictional flags
# into a composite feasibility score for the candidate site.

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_feasibility():
    return {"module": "feasibility", "status": "stub"}