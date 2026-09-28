import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.limiter import limiter

@pytest.fixture
def client():
    limiter.reset()
    with TestClient(app) as client:
        yield client
    limiter.reset()

@pytest.fixture
def resource_stub(monkeypatch):
    from app.api import resource, aep, lcoe, feasibility
    calls=[]
    async def fetch(lat,lon,height=100):
        calls.append((lat,lon,height))
        return {'lat':lat,'lon':lon,'height':height,'country':'NLD','mean_wind_speed':8.,'source':'TEST FIXTURE','note':'Synthetic test data'}
    for module in [resource,aep,lcoe,feasibility]:
        monkeypatch.setattr(module,'fetch_wind_resource',fetch)
    return calls
