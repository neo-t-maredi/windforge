import pytest
from app.api import resource,aep,lcoe,feasibility
from app.services.gwa import ResourceUnavailable

PARAMS={'lat':52.3,'lon':4.9,'height':100,'rated_power_kw':4200,'elevation_m':500,'temperature_c':35,'capex_per_mw_usd':1300000,'annual_opex_usd':100000,'terrain_complexity':1.3}


def test_health_root_and_cors(client):
    assert client.get('/health').json()['status']=='healthy'
    assert client.get('/').status_code==200
    allowed=client.options('/api/aep/',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
    assert allowed.headers['access-control-allow-origin']=='http://localhost:5173'
    denied=client.options('/api/aep/',headers={'Origin':'https://other.example','Access-Control-Request-Method':'GET'})
    assert 'access-control-allow-origin' not in denied.headers


def test_frontend_five_endpoint_contract_and_consistency(client,resource_stub):
    data={}
    for path in ['resource','aep','lcoe','capex','feasibility']:
        response=client.get(f'/api/{path}/',params=PARAMS)
        assert response.status_code==200,response.text
        data[path]=response.json()
    assert data['aep']['energy_production']==data['lcoe']['energy_production']==data['feasibility']['energy_production']
    assert data['lcoe']['financial_inputs']['capex_usd']==data['capex']['total_capex_usd']==data['feasibility']['financial']['total_capex_usd']
    assert data['lcoe']['lcoe']['lcoe_usd_per_mwh']==data['feasibility']['financial']['lcoe_usd_per_mwh']
    assert data['capex']['total_capex_usd']==7098000
    assert sum(data['capex']['cost_breakdown_usd'].values())==pytest.approx(7098000)
    assert 0 <= data['aep']['capacity_factor'] <= 1
    assert 0 <= data['feasibility']['feasibility_score'] <= 100
    assert data['feasibility']['feasibility_rating'] in ('Strong','Moderate','Weak')
    assert len(resource_stub)==4


def test_legacy_total_capex_takes_precedence(client,resource_stub):
    r=client.get('/api/lcoe/',params={**PARAMS,'capex_usd':1000000,'discount_rate':0})
    assert r.status_code==200,r.text
    assert r.json()['financial_inputs']['capex_usd']==1000000
    assert r.json()['lcoe']['capital_recovery_factor']==.05

@pytest.mark.parametrize('endpoint',['aep','lcoe','feasibility'])
def test_temperature_changes_each_energy_output(client,resource_stub,endpoint):
    cold=client.get(f'/api/{endpoint}/',params={**PARAMS,'temperature_c':0}).json()
    hot=client.get(f'/api/{endpoint}/',params={**PARAMS,'temperature_c':40}).json()
    assert cold['energy_production']['net_aep_mwh'] > hot['energy_production']['net_aep_mwh']

@pytest.mark.parametrize('endpoint',['resource','aep','lcoe','feasibility'])
@pytest.mark.parametrize('param,value',[('lat',91),('lon',-181),('lat','nan'),('height',75)])
def test_invalid_site(client,endpoint,param,value):
    assert client.get(f'/api/{endpoint}/',params={**PARAMS,param:value}).status_code==422

@pytest.mark.parametrize('endpoint',['aep','lcoe','capex','feasibility'])
@pytest.mark.parametrize('value',[0,-1,'nan','inf'])
def test_invalid_power(client,resource_stub,endpoint,value):
    assert client.get(f'/api/{endpoint}/',params={**PARAMS,'rated_power_kw':value}).status_code==422

@pytest.mark.parametrize('endpoint',['lcoe','feasibility'])
@pytest.mark.parametrize('param,value',[('annual_opex_usd',-1),('discount_rate',-1),('project_lifetime_years',0),('terrain_complexity',3)])
def test_invalid_financial_inputs(client,resource_stub,endpoint,param,value):
    assert client.get(f'/api/{endpoint}/',params={**PARAMS,param:value}).status_code==422


def test_invalid_curve_rejected_before_download(client,resource_stub):
    assert client.get('/api/aep/',params={**PARAMS,'cut_in':15,'rated_speed':12}).status_code==422
    assert resource_stub==[]

@pytest.mark.parametrize('module,path',[(resource,'resource'),(aep,'aep'),(lcoe,'lcoe'),(feasibility,'feasibility')])
@pytest.mark.parametrize('error,status',[(ValueError('Unsupported location'),422),(ResourceUnavailable('Upstream unavailable'),502)])
def test_resource_errors(client,monkeypatch,module,path,error,status):
    async def fail(**kwargs):raise error
    monkeypatch.setattr(module,'fetch_wind_resource',fail)
    response=client.get(f'/api/{path}/',params=PARAMS)
    assert response.status_code==status
    assert response.json()['detail']==str(error)


def test_feasibility_rate_limit(client,resource_stub):
    statuses=[client.get('/api/feasibility/',params=PARAMS).status_code for _ in range(11)]
    assert statuses==[200]*10+[429]

@pytest.mark.parametrize('speed,cost,cf,expected',[(7.5,35,.35,(100,'Strong')),(6,50,.25,(60,'Moderate')),(5.9,51,.24,(20,'Weak')),(7.49,35.01,.349,(60,'Moderate'))])
def test_feasibility_score_boundaries(speed,cost,cf,expected):
    assert feasibility.score_feasibility(speed,cost,cf)==expected


def test_custom_curve_consistency(client,resource_stub):
    p={**PARAMS,'cut_in':4,'rated_speed':10,'cut_out':22,'discount_rate':0,'project_lifetime_years':25}
    data=[client.get('/api/'+name+'/',params=p).json() for name in ['aep','lcoe','feasibility']]
    assert data[0]['energy_production']==data[1]['energy_production']==data[2]['energy_production']
    assert data[1]['lcoe']['lcoe_usd_per_mwh']==data[2]['financial']['lcoe_usd_per_mwh']


def test_http_to_raster_to_calculations(client,monkeypatch,tmp_path):
    """Only the external HTTP boundary is faked; routers, GeoTIFF and maths are real."""
    import httpx
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from app.services import gwa
    path=tmp_path/'fixture.tif'
    with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:4326',transform=from_origin(4,54,1,1)) as dst:
        dst.write(np.full((2,2),8,dtype='float32'),1)
    raw=path.read_bytes(); requests=[]; original=httpx.AsyncClient
    def handler(request):
        requests.append(request)
        return httpx.Response(200,content=raw)
    monkeypatch.setattr(gwa,'CACHE_DIR',tmp_path/'cache')
    monkeypatch.setattr(gwa.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    responses=[client.get('/api/'+name+'/',params=PARAMS) for name in ['resource','aep','lcoe','capex','feasibility']]
    assert all(r.status_code==200 for r in responses),[r.text for r in responses]
    assert responses[0].json()['mean_wind_speed']==8
    assert responses[1].json()['energy_production']==responses[4].json()['energy_production']
    assert len(requests)==1


def test_zero_yield_financials_are_validation_error(client,monkeypatch,resource_stub):
    async def low_wind(**kwargs):return {'mean_wind_speed':.01,'country':'NLD'}
    for module in [lcoe,feasibility]:monkeypatch.setattr(module,'fetch_wind_resource',low_wind)
    for endpoint in ['lcoe','feasibility']:
        response=client.get('/api/'+endpoint+'/',params=PARAMS)
        assert response.status_code==422
