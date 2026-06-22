// SiteForm.jsx
// Site parameters input form.
// Collects coordinates, turbine specs, and financial parameters
// then triggers the full analysis pipeline via the onRun callback.

function SiteForm({ params, setParams, onRun, loading }) {
  const update = (key, value) =>
    setParams(prev => ({ ...prev, [key]: parseFloat(value) || value }))

  return (
    <div className="site-form">
      <div className="form-section">
        <h2 className="form-section-title">Site Location</h2>
        <div className="form-row">
          <div className="form-group">
            <label>Latitude</label>
            <input
              type="number"
              step="0.001"
              value={params.lat}
              onChange={e => update("lat", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Longitude</label>
            <input
              type="number"
              step="0.001"
              value={params.lon}
              onChange={e => update("lon", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Hub Height (m)</label>
            <select
              value={params.height}
              onChange={e => update("height", e.target.value)}
            >
              <option value={50}>50m</option>
              <option value={100}>100m</option>
              <option value={200}>200m</option>
            </select>
          </div>
          <div className="form-group">
            <label>Elevation (m)</label>
            <input
              type="number"
              value={params.elevation_m}
              onChange={e => update("elevation_m", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Mean Temp (°C)</label>
            <input
              type="number"
              value={params.temperature_c}
              onChange={e => update("temperature_c", e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h2 className="form-section-title">Turbine Parameters</h2>
        <div className="form-row">
          <div className="form-group">
            <label>Rated Power (kW)</label>
            <input
              type="number"
              value={params.rated_power_kw}
              onChange={e => update("rated_power_kw", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Terrain Complexity</label>
            <select
              value={params.terrain_complexity}
              onChange={e => update("terrain_complexity", e.target.value)}
            >
              <option value={1.0}>1.0 — Flat / easy access</option>
              <option value={1.15}>1.15 — Gentle hills</option>
              <option value={1.3}>1.3 — Hilly / ridge</option>
              <option value={1.5}>1.5 — Mountainous / remote</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h2 className="form-section-title">Financial Parameters</h2>
        <div className="form-row">
          <div className="form-group">
            <label>CAPEX per MW (USD)</label>
            <input
              type="number"
              value={params.capex_per_mw_usd}
              onChange={e => update("capex_per_mw_usd", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Annual OPEX (USD/yr)</label>
            <input
              type="number"
              value={params.annual_opex_usd}
              onChange={e => update("annual_opex_usd", e.target.value)}
            />
          </div>
        </div>
      </div>

      <button
        className="run-btn"
        onClick={onRun}
        disabled={loading}
      >
        {loading ? "Running analysis..." : "⚡ Run Analysis"}
      </button>
    </div>
  )
}

export default SiteForm