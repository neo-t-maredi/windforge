# Dockerfile
# WindForge API container image.
# Uses a pre-built GDAL base image (ghcr.io/osgeo/gdal) to avoid
# compiling GDAL from source — cuts build time from 20+ minutes to
# under 2 minutes. rasterio installs cleanly against the pre-built
# GDAL libraries already in the image.

FROM ghcr.io/osgeo/gdal:ubuntu-small-latest

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

COPY . .

ENV APP_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]