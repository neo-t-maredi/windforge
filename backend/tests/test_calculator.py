import math
import pytest
from scipy.integrate import quad
from app.services import calculator as c


def test_standard_air_density_and_elevation():
    assert c.air_density(0, 15) == pytest.approx(1.225, abs=.001)
    assert c.air_density(1000, 15) < c.air_density(0, 15)
    assert c.air_density(0, 35) < c.air_density(0, 15)

@pytest.mark.parametrize('speed,expected', [(0,0),(3,0),(7.5,500),(12,1000),(24.9,1000),(25,0),(26,0)])
def test_power_curve_boundaries(speed, expected):
    assert c.simple_power_curve(speed, 1000) == expected

def test_weibull_normalizes():
    assert quad(lambda v:c.weibull_pdf(v,2,8),0,100)[0] == pytest.approx(1)

def test_aep_independent_midpoint_reference_and_scaling():
    # Independent discrete expectation checks integration and kWh->MWh conversion.
    n=20000; dv=25/n
    expected=sum(c.simple_power_curve((i+.5)*dv,1000)*2*((i+.5)*dv)/64*math.exp(-(((i+.5)*dv)/8)**2)*dv for i in range(n))*8.76
    value=c.calculate_gross_aep(2,8,1000)
    assert value == pytest.approx(expected,abs=.02)
    assert c.calculate_gross_aep(2,8,2000) == pytest.approx(2*value,abs=.02)

def test_density_correction_never_exceeds_generator_rating():
    assert 0 <= c.calculate_gross_aep(8,18,1000,2) <= 8760

def test_multiplicative_losses_and_empty_losses():
    result=c.apply_losses(1000,{'wake':.1,'electrical':.1})
    assert result['net_aep_mwh']==810
    assert result['total_loss_fraction']==.19
    assert c.apply_losses(1000,{})['net_aep_mwh']==1000

def test_returned_losses_do_not_mutate_defaults():
    r=c.apply_losses(1000); r['loss_breakdown']['wake']=.99
    assert c.DEFAULT_LOSSES['wake']==.08

def test_capacity_factor_units():
    assert c.capacity_factor(4380,1000)==.5

def test_lcoe_known_annuity():
    r=c.calculate_lcoe(1000000,20000,3000,.07,20)
    assert r['capital_recovery_factor']==pytest.approx(.0944,abs=.00005)
    assert r['lcoe_usd_per_mwh']==pytest.approx(38.13,abs=.01)

def test_zero_discount_rate():
    assert c.calculate_lcoe(1000000,20000,3000,0,20)['lcoe_usd_per_mwh']==pytest.approx(23.33)

@pytest.mark.parametrize('call',[
 lambda:c.air_density(0,-273.15),lambda:c.air_density(50000),
 lambda:c.air_density(float('nan')),lambda:c.air_density_correction_factor(-1),
 lambda:c.simple_power_curve(5,0),lambda:c.simple_power_curve(5,1000,12,3,25),
 lambda:c.calculate_gross_aep(0,8,1000),lambda:c.calculate_gross_aep(2,float('inf'),1000),
 lambda:c.apply_losses(-1),lambda:c.apply_losses(100,{'wake':1.1}),
 lambda:c.capacity_factor(1000,0),lambda:c.capacity_factor(9000,1000),
 lambda:c.calculate_lcoe(1,1,0),lambda:c.calculate_lcoe(-1,1,1),
 lambda:c.calculate_lcoe(1,1,1,-.1),lambda:c.calculate_lcoe(1,1,1,.07,0),
])
def test_invalid_calculator_inputs(call):
    with pytest.raises(ValueError):call()
