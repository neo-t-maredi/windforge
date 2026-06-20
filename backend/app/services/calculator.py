# calculator.py
# Core wind energy calculation engine.
# Implements IEC 61400-12-1 aligned methodology:
# - Air density correction for site elevation/temperature
# - Weibull-integrated AEP from GWA wind speed distribution
# - Parametric loss factor model (wake, availability, electrical, environmental)
# - LCOE calculation from net AEP and financial parameters
#
# Reference: IEC 61400-12-1:2017 Power performance measurements
# of electricity producing wind turbines

import math
from scipy import integrate
from scipy.stats import weibull_min

# Standard sea-level air density (kg/m^3) — power curves are rated at this density
RHO_STANDARD = 1.225

# Default loss factors (fraction lost, not retained) — typical onshore wind project
DEFAULT_LOSSES = {
    "wake": 0.08,           # internal + external array wake losses
    "availability": 0.03,   # turbine downtime, BOP maintenance
    "electrical": 0.02,     # collection system, transformer losses
    "environmental": 0.02,  # blade degradation, icing, curtailment
}


def air_density(elevation_m: float, temperature_c: float = 15.0) -> float:
    """
    Calculate site air density using the barometric formula and ideal gas law.
    Standard atmosphere assumption: lapse rate 0.0065 K/m, sea-level pressure 101325 Pa.

    Args:
        elevation_m: Site elevation above sea level in metres
        temperature_c: Site mean annual temperature in Celsius (default 15°C, ISA standard)

    Returns:
        Air density in kg/m^3
    """
    T0 = 288.15  # sea-level standard temperature (K)
    P0 = 101325  # sea-level standard pressure (Pa)
    L = 0.0065   # temperature lapse rate (K/m)
    R = 287.05   # specific gas constant for dry air (J/(kg·K))
    g = 9.80665  # gravitational acceleration (m/s^2)

    T_k = temperature_c + 273.15
    pressure = P0 * (1 - (L * elevation_m) / T0) ** (g / (R * L))
    rho = pressure / (R * T_k)

    return round(rho, 4)


def air_density_correction_factor(site_rho: float) -> float:
    """
    Returns the multiplier to apply to a sea-level-rated power curve
    to correct for actual site air density.
    """
    return site_rho / RHO_STANDARD


def weibull_pdf(v: float, k: float, a: float) -> float:
    """
    Weibull probability density function for wind speed v,
    given shape parameter k and scale parameter a (both from GWA).
    """
    return weibull_min.pdf(v, k, scale=a)


def simple_power_curve(v: float, rated_power_kw: float, cut_in: float = 3.0,
                         rated_speed: float = 12.0, cut_out: float = 25.0) -> float:
    """
    Simplified cubic power curve model for a generic turbine.
    Real OEM curves are non-linear lookup tables — this is an MVP
    approximation pending the turbine preset library.

    Returns power output in kW at wind speed v.
    """
    if v < cut_in or v > cut_out:
        return 0.0
    if v >= rated_speed:
        return rated_power_kw
    # Cubic ramp between cut-in and rated speed
    fraction = ((v - cut_in) / (rated_speed - cut_in)) ** 3
    return rated_power_kw * fraction


def calculate_gross_aep(weibull_k: float, weibull_a: float, rated_power_kw: float,
                          rho_correction: float = 1.0, cut_in: float = 3.0,
                          rated_speed: float = 12.0, cut_out: float = 25.0) -> float:
    """
    Calculate Gross Annual Energy Production by integrating the turbine
    power curve against the Weibull wind speed probability distribution.

    AEP = 8760 * integral[ P(v) * f(v) dv ] from 0 to cut_out

    Args:
        weibull_k: Weibull shape parameter (from GWA)
        weibull_a: Weibull scale parameter (from GWA)
        rated_power_kw: Turbine rated power in kW
        rho_correction: Air density correction factor (site_rho / 1.225)
        cut_in, rated_speed, cut_out: Turbine operational wind speeds (m/s)

    Returns:
        Gross AEP in MWh/year
    """
    def integrand(v):
        power = simple_power_curve(v, rated_power_kw, cut_in, rated_speed, cut_out)
        power_corrected = power * rho_correction
        density = weibull_pdf(v, weibull_k, weibull_a)
        return power_corrected * density

    expected_power_kw, _ = integrate.quad(integrand, 0, cut_out + 5)
    gross_aep_kwh = expected_power_kw * 8760
    gross_aep_mwh = gross_aep_kwh / 1000

    return round(gross_aep_mwh, 2)


def apply_losses(gross_aep_mwh: float, losses: dict = None) -> dict:
    """
    Apply parametric loss factors to gross AEP to derive net AEP.
    Losses are applied multiplicatively (industry standard practice).

    Args:
        gross_aep_mwh: Gross annual energy production in MWh
        losses: dict of loss category -> fraction lost (default: DEFAULT_LOSSES)

    Returns:
        dict with gross_aep, net_aep, total_loss_fraction, loss_breakdown
    """
    if losses is None:
        losses = DEFAULT_LOSSES

    retained_fraction = 1.0
    for category, loss_fraction in losses.items():
        retained_fraction *= (1 - loss_fraction)

    net_aep_mwh = gross_aep_mwh * retained_fraction
    total_loss_fraction = 1 - retained_fraction

    return {
        "gross_aep_mwh": round(gross_aep_mwh, 2),
        "net_aep_mwh": round(net_aep_mwh, 2),
        "total_loss_fraction": round(total_loss_fraction, 4),
        "loss_breakdown": losses,
    }


def capacity_factor(net_aep_mwh: float, rated_power_kw: float) -> float:
    """
    Calculate capacity factor: actual energy produced vs theoretical
    maximum if running at rated power 100% of the time.
    """
    max_possible_mwh = (rated_power_kw / 1000) * 8760
    return round(net_aep_mwh / max_possible_mwh, 4)


def calculate_lcoe(capex: float, annual_opex: float, net_aep_mwh: float,
                     discount_rate: float = 0.07, project_lifetime_years: int = 20) -> dict:
    """
    Calculate Levelised Cost of Energy using the Capital Recovery Factor method.

    LCOE = (CAPEX * CRF + Annual OPEX) / Net AEP
    CRF  = r(1+r)^n / ((1+r)^n - 1)

    Args:
        capex: Total capital expenditure (USD)
        annual_opex: Annual operating expenditure (USD/year)
        net_aep_mwh: Net annual energy production (MWh/year)
        discount_rate: Discount rate as decimal (default 7%)
        project_lifetime_years: Project lifetime in years (default 20)

    Returns:
        dict with lcoe_usd_per_mwh, crf, annualized_capex
    """
    r = discount_rate
    n = project_lifetime_years

    crf = (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    annualized_capex = capex * crf

    lcoe = (annualized_capex + annual_opex) / net_aep_mwh

    return {
        "lcoe_usd_per_mwh": round(lcoe, 2),
        "capital_recovery_factor": round(crf, 4),
        "annualized_capex_usd": round(annualized_capex, 2),
    }