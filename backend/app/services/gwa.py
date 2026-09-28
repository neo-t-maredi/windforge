"""Country-raster screening adapter. Bounding-box selection is approximate, not a boundary lookup."""
import asyncio
import math
import os
import tempfile
from pathlib import Path
import httpx
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window

from app.core.config import settings

GWA_RASTER_BASE = settings.GWA_API_BASE_URL.rstrip("/")
VALID_HEIGHTS = [50,100,200]
CACHE_DIR = Path(tempfile.gettempdir()) / 'windforge_gwa_cache'

class ResourceUnavailable(ValueError):
    """Upstream download or malformed raster failure (HTTP 502)."""


def _get_iso3(lat, lon):
    if 50.5 <= lat <= 53.7 and 3.2 <= lon <= 7.3:
        return 'NLD'
    if 16 <= lat <= 32.5 and 34.5 <= lon <= 55.7:
        return 'SAU'
    raise ValueError('Location is outside the currently supported raster lookup regions')


async def _download_raster(iso3, variable, height):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = CACHE_DIR / f'{iso3}_{variable}_{height}m.tif'
    if target.exists():
        return target
    url = f'{GWA_RASTER_BASE}/{iso3}/{variable}/{height}'
    temporary = None
    try:
        async with httpx.AsyncClient(timeout=60., follow_redirects=True) as client:
            # Stream country rasters instead of holding entire downloads in memory.
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(dir=CACHE_DIR, suffix='.part', delete=False) as f:
                    temporary = Path(f.name)
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        with rasterio.open(temporary) as src:
            if src.count < 1 or src.crs is None:
                raise ResourceUnavailable('Raster has no band or coordinate reference system')
        os.replace(temporary, target)  # Readers never observe an incomplete cache file.
        return target
    except (httpx.HTTPError, rasterio.errors.RasterioError, OSError) as exc:
        raise ResourceUnavailable('Wind resource download failed or returned an invalid raster') from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _sample_raster(filepath, lat, lon):
    try:
        with rasterio.open(filepath) as src:
            if src.crs is None:
                raise ResourceUnavailable('Raster coordinate reference system is missing')
            xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
            row, col = src.index(xs[0],ys[0])
            if not (0 <= row < src.height and 0 <= col < src.width):
                raise ValueError('Location is outside the available wind raster')
            pixel = src.read(1, window=Window(col,row,1,1), masked=True)
            if pixel.mask.any():
                raise ValueError('No wind data for this location')
            value = float(pixel[0,0])
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Wind speed must be finite and positive at this location')
            return value
    except (rasterio.errors.RasterioError, OSError) as exc:
        raise ResourceUnavailable('Cached wind raster is unreadable; remove it and retry') from exc


async def fetch_wind_resource(lat, lon, height=100):
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('Coordinates must be finite and within geographic bounds')
    if height not in VALID_HEIGHTS:
        raise ValueError(f'Height must be one of {VALID_HEIGHTS} m')
    iso3 = _get_iso3(lat,lon)
    path = await _download_raster(iso3,'wind-speed',height)
    speed = await asyncio.to_thread(_sample_raster,path,lat,lon)
    return {'lat':lat,'lon':lon,'height':height,'country':iso3,'mean_wind_speed':speed,
            'source':'Global Wind Atlas country wind-speed raster',
            'note':'Screening only. Country selected by approximate bounding boxes, not verified political boundaries. On-site measurement required.'}
