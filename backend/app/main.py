# main.py
# WindForge API entry point.
# Initialises the FastAPI application, configures CORS middleware,
# and registers all route modules. Each module handles a distinct
# stage of the wind site feasibility assessment pipeline:
# resource → aep → lcoe → capex → feasibility.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import resource, aep, lcoe, capex, feasibility

app = FastAPI(
    title="WindForge API",
    description="Wind site feasibility analysis — AEP, LCOE, CAPEX modelling",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resource.router, prefix="/api/resource", tags=["Wind Resource"])
app.include_router(aep.router, prefix="/api/aep", tags=["AEP"])
app.include_router(lcoe.router, prefix="/api/lcoe", tags=["LCOE"])
app.include_router(capex.router, prefix="/api/capex", tags=["CAPEX"])
app.include_router(feasibility.router, prefix="/api/feasibility", tags=["Feasibility"])

@app.get("/")
def root():
    return {"status": "WindForge API is live"}