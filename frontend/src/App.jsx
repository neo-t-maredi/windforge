// App.jsx
// WindForge frontend entry point.
// Manages global state and orchestrates the analysis pipeline:
// SiteForm (inputs) → API calls → ResultsDashboard (outputs)

import { useState } from "react"
import SiteForm from "./components/SiteForm"
import ResultsDashboard from "./components/ResultsDashboard"
import "./App.css"

const API_BASE = "http://127.0.0.1:8000"

const DEFAULT_PARAMS = {
  lat: 52.3,
  lon: 4.9,
  height: 100,
  rated_power_kw: 4200,
  elevation_m: 0,
  temperature_c: 15,
  capex_per_mw_usd: 1300000,
  annual_opex_usd: 100000,
  terrain_complexity: 1.0,
}

function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runAnalysis = async () => {
    setLoading(true)
    setError(null)
    setResults(null)

    const q = new URLSearchParams(params).toString()

    try {
      const [resource, aep, lcoe, capex, feasibility] = await Promise.all([
        fetch(`${API_BASE}/api/resource/?lat=${params.lat}&lon=${params.lon}&height=${params.height}`).then(r => r.json()),
        fetch(`${API_BASE}/api/aep/?${q}`).then(r => r.json()),
        fetch(`${API_BASE}/api/lcoe/?${q}`).then(r => r.json()),
        fetch(`${API_BASE}/api/capex/?rated_power_kw=${params.rated_power_kw}&capex_per_mw_usd=${params.capex_per_mw_usd}&terrain_complexity=${params.terrain_complexity}`).then(r => r.json()),
        fetch(`${API_BASE}/api/feasibility/?${q}`).then(r => r.json()),
      ])

      setResults({ resource, aep, lcoe, capex, feasibility })
    } catch (err) {
      setError("API connection failed — is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="brand-icon">
            <path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/>
            <path d="M9.6 4.6A2 2 0 1 1 11 8H2"/>
            <path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>
          </svg>
          <h1>WindForge</h1>
          <span className="version-tag">v0.1.0</span>
        </div>
        <div className="header-right">
          <span className="api-status">⚡ API live</span>
        </div>
      </header>

      <main className="app-main">
        <SiteForm
          params={params}
          setParams={setParams}
          onRun={runAnalysis}
          loading={loading}
        />
        {error && <div className="error-banner">{error}</div>}
        {results && <ResultsDashboard results={results} />}
        {!results && !loading && (
          <div className="empty-state">
            Enter site coordinates and hit Run Analysis to begin.
          </div>
        )}
        {loading && (
          <div className="loading-state">
            Fetching wind resource data and running calculations...
          </div>
        )}
      </main>
    </div>
  )
}

export default App