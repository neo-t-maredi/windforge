# gwa.py
# Global Wind Atlas raster service layer.
# GWA distributes wind resource data as country-level GeoTIFF rasters
# at 250m resolution, not as a point-query JSON API. This service
# downloads the relevant raster for a country and samples the pixel
# value at the given lat/lon using rasterio.
#
# Note: GWA is a screening/pre-feasibility tool, not a bankable data
# source. Real project finance requires 1-2 years of on-site
# measurement data (see globalwindatlas.info FAQ).

import httpx
import rasterio
import tempfile
from pathlib import Path

GWA_RASTER_BASE = "https://globalwindatlas.info/api/gis/country"
VALID_HEIGHTS = [50, 100, 200]
CACHE_DIR = Path(tempfile.gettempdir()) / "windforge_gwa_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _get_iso3(lat: float, lon: float) -> str:
    """
    Reverse geocode lat/lon to ISO3 country code.
    Uses a simple bounding-box approach for MVP — replace with
    a proper reverse geocoder (e.g. reverse_geocoder lib) for production.
    """
    # MVP placeholder: Netherlands bounding box for Rotterdam-area testing
    if 50.5 <= lat <= 53.7 and 3.2 <= lon <= 7.3:
        return "NLD"
    if 16.0 <= lat <= 32.5 and 34.5 <= lon <= 55.7:
        return "SAU"
    raise ValueError(f"Country lookup not yet implemented for lat={lat}, lon={lon}")


async def _download_raster(iso3: str, variable: str, height: int) -> Path:
    """
    Download a GWA GeoTIFF raster for a country if not already cached.
    """
    filename = f"{iso3}_{variable}_{height}m.tif"
    filepath = CACHE_DIR / filename

    if filepath.exists():
        return filepath

    url = f"{GWA_RASTER_BASE}/{iso3}/{variable}/{height}"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        filepath.write_bytes(response.content)

    return filepath


def _sample_raster(filepath: Path, lat: float, lon: float) -> float:
    """
    Sample a raster file at the given coordinates and return the pixel value.
    """
    with rasterio.open(filepath) as src:
        row, col = src.index(lon, lat)
        band = src.read(1)
        value = band[row, col]
        return float(value)


async def fetch_wind_resource(lat: float, lon: float, height: int = 100) -> dict:
    """
    Fetch wind resource data for a candidate site by downloading the
    relevant GWA country raster and sampling the pixel at lat/lon.
    """
    if height not in VALID_HEIGHTS:
        raise ValueError(f"Height must be one of {VALID_HEIGHTS}m")

    iso3 = _get_iso3(lat, lon)

    try:
        speed_path = await _download_raster(iso3, "wind-speed", height)
        mean_wind_speed = _sample_raster(speed_path, lat, lon)
    except httpx.HTTPStatusError as e:
        raise ValueError(f"GWA raster download failed: {e.response.status_code}")
    except httpx.RequestError as e:
        raise ValueError(f"GWA connection error: {str(e)}")

    return {
        "lat": lat,
        "lon": lon,
        "height": height,
        "country": iso3,
        "mean_wind_speed": round(mean_wind_speed, 2),
        "source": "Global Wind Atlas v3 (DTU / World Bank)",
        "note": "Pre-feasibility screening data only — not bankable without on-site measurement"
    }