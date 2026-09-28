import asyncio
import math
import numpy as np
import pytest
import httpx
import rasterio
from rasterio.transform import from_origin
from app.services import gwa


def write_raster(path,values=None,crs='EPSG:4326',transform=None):
    values=np.array([[7.,8.],[9.,-9999.]] if values is None else values,dtype='float32')
    with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs=crs,transform=transform or from_origin(4,54,1,1),nodata=-9999) as dst:
        dst.write(values,1)
    return path


def test_sample_exact_pixel_and_projected_crs(tmp_path):
    path=write_raster(tmp_path/'geo.tif')
    assert gwa._sample_raster(path,53.5,4.5)==7
    projected=write_raster(tmp_path/'proj.tif',crs='EPSG:3857',transform=from_origin(0,2000,1000,1000))
    from rasterio.warp import transform
    lon,lat=transform('EPSG:3857','EPSG:4326',[500],[1500])
    assert gwa._sample_raster(projected,lat[0],lon[0])==7

@pytest.mark.parametrize('lat,lon',[(54.1,4.5),(51.9,4.5),(53.5,3.9),(53.5,6),(52.5,5.5)])
def test_outside_and_nodata_never_wrap_to_other_pixel(tmp_path,lat,lon):
    with pytest.raises(ValueError):gwa._sample_raster(write_raster(tmp_path/'x.tif'),lat,lon)

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-2,0])
def test_invalid_pixel(tmp_path,value):
    path=write_raster(tmp_path/'x.tif',[[value,8],[9,10]])
    with pytest.raises(ValueError):gwa._sample_raster(path,53.5,4.5)


def test_corrupt_raster(tmp_path):
    path=tmp_path/'bad.tif';path.write_text('not a raster')
    with pytest.raises(gwa.ResourceUnavailable):gwa._sample_raster(path,53.5,4.5)

@pytest.mark.parametrize('args',[(100,4,100),(52,200,100),(math.nan,4,100),(52,4,75),(0,0,100)])
def test_invalid_location_before_network(args):
    with pytest.raises(ValueError):asyncio.run(gwa.fetch_wind_resource(*args))


def mock_transport(monkeypatch,tmp_path,handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(gwa,'CACHE_DIR',tmp_path/'cache')
    monkeypatch.setattr(gwa.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))


def test_download_cache_and_full_resource_pipeline(monkeypatch,tmp_path):
    content=write_raster(tmp_path/'fixture.tif').read_bytes();requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,content=content)
    mock_transport(monkeypatch,tmp_path,handler)
    result=asyncio.run(gwa.fetch_wind_resource(53.5,4.5,100))
    assert result['mean_wind_speed']==7
    assert result['country']=='NLD'
    asyncio.run(gwa.fetch_wind_resource(53.5,4.5,100))
    assert len(requests)==1
    assert list(gwa.CACHE_DIR.glob('*.part'))==[]

@pytest.mark.parametrize('mode',['http','timeout','invalid'])
def test_failed_download_leaves_no_cache(monkeypatch,tmp_path,mode):
    def handler(request):
        if mode=='timeout':raise httpx.ReadTimeout('timed out',request=request)
        return httpx.Response(503 if mode=='http' else 200,content=b'bad data')
    mock_transport(monkeypatch,tmp_path,handler)
    with pytest.raises(gwa.ResourceUnavailable):asyncio.run(gwa._download_raster('NLD','wind-speed',100))
    assert list(gwa.CACHE_DIR.iterdir())==[]
