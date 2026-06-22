// ResultsDashboard.jsx
// Results display component.
// Renders the full analysis output from all five WindForge API
// endpoints: wind resource, AEP, LCOE, CAPEX, and feasibility.

function Metric({ label, value, unit, highlight }) {
  return (
    <div className={`metric ${highlight ? "metric-highlight" : ""}`}>
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
      {unit && <span className="metric-unit">{unit}</span>}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="result-section">
      <h3 className="result-section-title">{title}</h3>
      <div className="result-section-content">{children}</div>
    </div>
  )
}

function FeasibilityScore({ score, rating }) {
  const color = rating === "Strong" ? "#00ff88" : rating === "Moderate" ? "#ffaa00" : "#ff4444"
  return (
    <div className="feasibility-score" style={{ borderColor: color }}>
      <span className="score-number" style={{ color }}>{score}</span>
      <span className="score-label">/ 100</span>
      <span className="score-rating" style={{ color }}>{rating}</span>
    </div>
  )
}

function ResultsDashboard({ results }) {
  const { resource, aep, lcoe, capex, feasibility } = results

  return (
    <div className="results-dashboard">

      <Section title="Wind Resource">
        <div className="metrics-grid">
          <Metric label="Mean Wind Speed" value={resource.mean_wind_speed} unit="m/s" highlight />
          <Metric label="Country" value={resource.country} />
          <Metric label="Hub Height" value={resource.height} unit="m" />
        </div>
        <p className="data-note">{resource.note}</p>
      </Section>

      <Section title="Annual Energy Production">
        <div className="metrics-grid">
          <Metric label="Gross AEP" value={aep.energy_production.gross_aep_mwh.toLocaleString()} unit="MWh/yr" />
          <Metric label="Net AEP" value={aep.energy_production.net_aep_mwh.toLocaleString()} unit="MWh/yr" highlight />
          <Metric label="Capacity Factor" value={(aep.capacity_factor * 100).toFixed(1)} unit="%" highlight />
          <Metric label="Total Losses" value={(aep.energy_production.total_loss_fraction * 100).toFixed(1)} unit="%" />
          <Metric label="Air Density" value={aep.site_conditions.air_density_kg_m3} unit="kg/m³" />
          <Metric label="Weibull A" value={aep.wind_resource.weibull_a_derived} />
        </div>
      </Section>

      <Section title="Levelised Cost of Energy">
        <div className="metrics-grid">
          <Metric label="LCOE" value={lcoe.lcoe?.lcoe_usd_per_mwh?.toFixed(2) ?? "—"} unit="USD/MWh" highlight />
          <Metric label="Capital Recovery Factor" value={((lcoe.lcoe?.capital_recovery_factor ?? 0) * 100).toFixed(2)} unit="%" />
          <Metric label="Annualised CAPEX" value={`$${(lcoe.lcoe?.annualized_capex_usd ?? 0).toLocaleString()}`} />
        </div>
      </Section>

      <Section title="Capital Expenditure">
        <div className="metrics-grid">
          <Metric label="Total CAPEX" value={`$${capex.total_capex_usd.toLocaleString()}`} highlight />
          <Metric label="Turbine Supply" value={`$${capex.cost_breakdown_usd.turbine_supply.toLocaleString()}`} />
          <Metric label="Balance of Plant" value={`$${capex.cost_breakdown_usd.balance_of_plant.toLocaleString()}`} />
          <Metric label="Grid Connection" value={`$${capex.cost_breakdown_usd.grid_connection.toLocaleString()}`} />
          <Metric label="Soft Costs" value={`$${capex.cost_breakdown_usd.soft_costs.toLocaleString()}`} />
        </div>
      </Section>

      <Section title="Site Feasibility">
        <FeasibilityScore
          score={feasibility.feasibility_score}
          rating={feasibility.feasibility_rating}
        />
        <div className="jurisdiction-flags">
          <div className="flag-item">
            <span className="flag-label">Permitting</span>
            <span className="flag-value">{feasibility.jurisdiction.permitting_complexity}</span>
          </div>
          <div className="flag-item">
            <span className="flag-label">Grid Connection</span>
            <span className="flag-value">{feasibility.jurisdiction.grid_connection_outlook}</span>
          </div>
          <div className="flag-item">
            <span className="flag-label">Policy</span>
            <span className="flag-value">{feasibility.jurisdiction.renewable_policy}</span>
          </div>
          <div className="flag-item">
            <span className="flag-label">Typical Timeline</span>
            <span className="flag-value">{feasibility.jurisdiction.typical_timeline_months} months</span>
          </div>
        </div>
        <p className="data-note">{feasibility.note}</p>
      </Section>

    </div>
  )
}

export default ResultsDashboard