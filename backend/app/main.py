# main.py
# WindForge API entry point.
# Initialises the FastAPI application, configures CORS middleware,
# structured logging, rate limiting, and registers all route modules.
# Each module handles a distinct stage of the wind site feasibility
# assessment pipeline: resource → aep → lcoe → capex → feasibility.

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.api import resource, aep, lcoe, capex, feasibility
from app.core.logging_setup import configure_logging, logger

# Configure structured logging before anything else starts
configure_logging()

# Rate limiter — keyed by client IP, applied per-route via decorators
#limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="WindForge API",
    description="Wind site feasibility analysis — AEP, LCOE, CAPEX modelling",
    version="0.1.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Structured request/response logging middleware.
    Logs method, path, client IP, and response status for every request.
    """
    logger.info(
        "request_received",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    response = await call_next(request)
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


app.include_router(resource.router, prefix="/api/resource", tags=["Wind Resource"])
app.include_router(aep.router, prefix="/api/aep", tags=["AEP"])
app.include_router(lcoe.router, prefix="/api/lcoe", tags=["LCOE"])
app.include_router(capex.router, prefix="/api/capex", tags=["CAPEX"])
app.include_router(feasibility.router, prefix="/api/feasibility", tags=["Feasibility"])


@app.get("/")
def root():
    return {"status": "WindForge API is live"}


@app.get("/health")
def health_check():
    """
    Health check endpoint for uptime monitoring and deployment
    orchestration (e.g. Docker healthcheck, load balancer probes).
    """
    return {
        "status": "healthy",
        "service": "windforge-api",
        "version": "0.1.0"
    }