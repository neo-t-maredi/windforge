# WindForge backend: review and tests

## Install and run

Use Python 3.12 (the version used for this review). From the backend directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest --cov=app --cov-branch --cov-report=term-missing
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend connects to http://127.0.0.1:8000 by default. CORS allows localhost:5173 and 127.0.0.1:5173. The standalone HTML preview may have a null origin; use the Vite frontend for API integration.

## Verified result

115 tests passed on Python 3.12.14. Coverage including branches: 97% (348 statements, 76 branches). The test runner emitted 14 third-party deprecation warnings from Starlette's httpx adapter and Rasterio/Affine. There were no test failures. Coverage is not evidence that the engineering model is validated.

- Unit: air density, distribution normalization, power curve boundaries, independent numerical expectation, energy units and scaling, loss multiplication, capacity factor, CRF, zero-interest LCOE, invalid inputs and feasibility thresholds.
- API integration: five frontend endpoints, consistent AEP/CAPEX/LCOE across endpoints, temperature and custom power curve propagation, legacy total CAPEX input, validation, upstream failures, zero yield, CORS and rate limiting.
- Raster integration: real temporary GeoTIFFs, geographic/projected CRS, out-of-bounds pixels, nodata/nonfinite/negative/zero values, download cache, HTTP errors, timeouts and invalid files.
- End-to-end backend integration: actual HTTP routes, raster decoding/sampling and calculations, with only the external HTTP download replaced by a deterministic fixture.

Tests are deterministic and do not require Global Wind Atlas. They do not test a real browser or actual GWA availability.

## Defects fixed

1. LCOE previously required capex_usd although the frontend sends capex_per_mw_usd. It now derives total CAPEX using turbine MW and terrain complexity when an explicit total is absent. Explicit capex_usd takes precedence for backwards compatibility.
2. Feasibility ignored temperature. Temperature, turbine curve parameters, discount rate and lifetime are now used consistently by the relevant endpoints.
3. Zero discount rate divided by zero. CRF now uses 1/lifetime at zero and a numerically stable annuity formula otherwise.
4. Density correction could exceed generator nameplate power. Corrected output is capped; output shuts down at the cut-out speed, inclusive.
5. Missing calculation/API input guards allowed nonsensical values and divide-by-zero errors. Domain errors now return HTTP 422; upstream failures return 502. Zero net energy is invalid for LCOE rather than returning infinity or zero cost.
6. Raster sampling loaded whole countries, assumed geographic CRS, allowed negative array indexing and ignored nodata. It now transforms coordinates, bounds-checks, reads one pixel and rejects invalid values.
7. Downloads could expose partial cache files. Streaming writes now use unique temporary files, validate the raster and atomically replace the target. Concurrent cold requests may still duplicate downloads, but cannot expose partial cache files.
8. Returning default loss dictionaries allowed accidental global mutation. Results return a copy.
9. requirements.txt was empty. Runtime and test dependencies now list the exact direct versions exercised. Transitive dependencies are not locked.
10. The configured GWA URL was unused and pointed elsewhere. The adapter now uses GWA_API_BASE_URL; the default retains the original adapter's country-raster URL.

## Scope and remaining limitations

- No live GWA URL, raster version or production availability was verified. The upstream service may require a different endpoint or configuration.
- Country selection still uses the original Netherlands/Saudi bounding boxes. These are not country borders and can select a neighbouring country's territory. Responses explicitly disclose this limitation; real geographic boundary lookup remains future work.
- Synthetic smoothstep turbine curve, assumed Weibull k=2 and fixed losses remain demo assumptions. These tests verify implementation, not IEC compliance, OEM accuracy or bankability.
- Existing wake loss is 8% even when modelling a single turbine; assess site-specific losses before interpreting results.
- Jurisdiction strings remain unverified demo content and may be stale. Responses label them accordingly.
- No browser, live remote service, Docker image build or load test was run. Docker's original floating GDAL base tag remains unchanged.
- No disk-cache eviction or cross-process download deduplication was added.

## Apply safely

Back up your existing backend directory and replace only that directory with the updated backend from this archive. The archive retains the other original uploaded files, including the older frontend; do not copy that frontend over the redesigned frontend you approved. Existing frontend request/response names are preserved. The intentional behaviour changes are listed above.
