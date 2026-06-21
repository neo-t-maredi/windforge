# Dockerfile
# WindForge API container image.
# Multi-stage build: install dependencies in a build layer, copy only
# what's needed into a slim runtime image to keep the final image small.

FROM python:3.12-slim AS builder

WORKDIR /app

# System dependencies needed to build rasterio (GDAL bindings)
RUN apt-get update && apt-get install -y \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# GDAL runtime libraries required by rasterio at runtime
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV APP_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]