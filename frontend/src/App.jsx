import { useEffect, useState } from 'react'
import SiteForm from './components/SiteForm'
import ResultsDashboard from './components/ResultsDashboard'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const DEFAULT_PARAMS = { lat: 52.3, lon: 4.9, height: 100, rated_power_kw: 4200, elevation_m: 0, temperature_c: 15, capex_per_mw_usd: 1300000, annual_opex_usd: 100000, terrain_complexity: 1 }

function TurbineScene() {
  return <svg className="turbine-scene" viewBox="0 0 660 360" aria-hidden="true">
    <defs><linearGradient id="blade"><stop stopColor="#fff7df"/><stop offset="1" stopColor="#91a398"/></linearGradient><pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="currentColor" strokeOpacity=".09"/></pattern></defs>
    <rect width="660" height="360" fill="url(#grid)"/>
    <g className="orbit"><circle cx="400" cy="153" r="130" fill="none" stroke="currentColor" strokeOpacity=".2" strokeDasharray="2 8"/><circle cx="400" cy="23" r="4" fill="#d6ed89"/></g>
    <g fill="none" stroke="currentColor" strokeOpacity=".2"><path d="M0 306Q150 240 310 309T660 294"/><path d="M0 325Q180 278 350 325T660 313"/><path d="M0 341Q190 308 365 341T660 329"/></g>
    {[65,120,205,255].map((y,i)=><path key={y} className="wind-trace" style={{animationDelay:`-${i * 1.3}s`}} d={`M0 ${y} Q170 ${y-35} 320 ${y} T660 ${y}`} fill="none" stroke="#d6ed89" strokeWidth="1.4" strokeDasharray="50 700"/>)}
    <g opacity=".4" transform="translate(150 173) scale(.53)"><path d="M-4 0L-10 230H10L4 0" fill="url(#blade)"/><g className="rotor-small">{[0,120,240].map(a=><path key={a} transform={`rotate(${a})`} d="M-5 0 C-18-45-4-111 1-136 C9-109 13-48 5 0Z" fill="url(#blade)"/>)}</g><circle r="8" fill="#eaf0df"/></g>
    <g transform="translate(400 153)"><path d="M-5 0L-12 176H12L5 0" fill="url(#blade)"/><path d="M0 8V171" stroke="#70867c"/><g className="rotor">{[0,120,240].map(a=><path key={a} transform={`rotate(${a})`} d="M-5 0 C-21-47-5-113 1-137 C8-117 14-56 6-3Z" fill="url(#blade)" stroke="#f3f0dd" strokeWidth=".5"/>)}</g><circle r="10" fill="#d6ed89"/><circle r="4" fill="#23362e"/></g>
    <path d="M448 153H504M492 148L504 153L492 158M504 153V328M496 328H512" fill="none" stroke="currentColor" strokeOpacity=".4"/>
    <text x="518" y="247" fill="currentColor" fontSize="10" letterSpacing="2">HUB</text><text x="22" y="340" fill="currentColor" fontSize="9" letterSpacing="2">CONCEPTUAL TURBINE VIEW · NOT TO SCALE</text>
  </svg>
}

export default function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [results, setResults] = useState(null)
  const [submitted, setSubmitted] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState('Checking API')
  const [theme, setTheme] = useState('dark')
  const [motion, setMotion] = useState(true)
  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    fetch(`${API_BASE}/health`, { signal: controller.signal }).then(r => setStatus(r.ok ? 'API connected' : 'API unavailable')).catch(() => setStatus('API unavailable'))
    return () => { clearTimeout(timer); controller.abort() }
  }, [])
  const runAnalysis = async () => {
    setLoading(true); setError(null)
    const snapshot = { ...params }
    const q = new URLSearchParams(snapshot).toString()
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 60000)
    const get = async path => {
      const r = await fetch(`${API_BASE}${path}`, { signal: controller.signal })
      if (!r.ok) throw new Error(`Analysis request failed (${r.status}). Check the inputs and try again.`)
      return r.json()
    }
    try {
      const [resource, aep, lcoe, capex, feasibility] = await Promise.all([
        get(`/api/resource/?lat=${snapshot.lat}&lon=${snapshot.lon}&height=${snapshot.height}`), get(`/api/aep/?${q}`), get(`/api/lcoe/?${q}`),
        get(`/api/capex/?rated_power_kw=${snapshot.rated_power_kw}&capex_per_mw_usd=${snapshot.capex_per_mw_usd}&terrain_complexity=${snapshot.terrain_complexity}`), get(`/api/feasibility/?${q}`),
      ])
      setResults({ resource, aep, lcoe, capex, feasibility }); setSubmitted(snapshot); setStatus('API connected')
    } catch (err) {
      controller.abort()
      setError(err.name === 'AbortError' ? 'The analysis timed out. Please try again.' : err instanceof TypeError ? 'Cannot reach the analysis service. Check that the backend is running on the configured API address.' : err.message)
      setStatus('Request failed')
    } finally { clearTimeout(timer); setLoading(false) }
  }
  const stale = results && JSON.stringify(params) !== JSON.stringify(submitted)
  return <div className="app" data-theme={theme} data-motion={motion ? 'on' : 'off'}>
    <header className="app-header"><a className="brand" href="#"><span className="brand-mark">↗</span>windforge<span className="version-tag">/ 01</span></a><span className="header-caption">WIND RESOURCE INTELLIGENCE</span><div className="header-actions"><span className={`api-status ${status === 'API connected' ? 'connected' : ''}`}><i/>{status}</span><button className="icon-btn" onClick={()=>setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? '☼' : '☾'}</button></div></header>
    <main>
      <section className="hero"><div className="hero-copy"><span className="eyebrow"><span/> FROM RESOURCE TO RETURN</span><h1>Find the potential.<br/><em>Follow the wind.</em></h1><p>Explore the energy and economics of a wind site.<br className="desktop-break"/> Your assumptions. A clearer starting point.</p><a className="text-link" href="#workspace">Build your assessment <span>↘</span></a></div><div className="hero-visual"><TurbineScene/><div className="scene-caption"><span>WIND / MOTION STUDY</span><button onClick={()=>setMotion(!motion)} aria-pressed={!motion}>{motion ? 'Ⅱ Pause motion' : '▷ Resume motion'}</button></div></div></section>
      <div className="workspace-heading" id="workspace"><div><span className="eyebrow">SITE ASSESSMENT</span><h2>From the ground up.</h2></div><span className="workspace-note">01 / Configure <span>→</span> 02 / Evaluate</span></div>
      <div className="workspace"><aside><SiteForm params={params} setParams={setParams} onRun={runAnalysis} loading={loading}/></aside><section className="analysis" aria-label="Analysis results" aria-busy={loading}><div className="analysis-heading"><h2>Analysis overview</h2><span className="small-label">{loading ? 'CALCULATING' : stale ? 'INPUTS CHANGED' : results ? 'COMPLETE' : 'AWAITING FIRST RUN'}</span></div>
      {error && <div className="error-banner" role="alert">{error}</div>}
      {stale && <p className="stale-note">These results use your previous inputs. Run analysis to update them.</p>}
      {loading && <div className="loading-state" role="status"><span className="loading-ring"/>Retrieving wind resource and calculating site economics…</div>}
      {results ? <ResultsDashboard results={results}/> : <div className="empty-state"><div className="empty-metrics">{['NET ANNUAL ENERGY','CAPACITY FACTOR','LEVELISED COST'].map(t=><div key={t}><span>{t}</span><strong>—</strong><small>Available after analysis</small></div>)}</div><div className="awaiting"><div className="compass"><span>N</span><i/><b>↗</b></div><span className="eyebrow">A SITE. A SET OF POSSIBILITIES.</span><h3>Your next project starts here.</h3><p>Set your coordinates, turbine and cost assumptions.<br/>Run an assessment to reveal the site's potential.</p><div className="output-tags"><span>Wind resource</span><span>Energy yield</span><span>Project economics</span></div></div><p className="analysis-note">Preliminary screening · Review model assumptions and source notes before using results.</p></div>}
      </section></div>
    </main><footer><span>windforge <span className="footer-slash">/</span> Engineering the energy transition.</span><span>RESOURCE → ENERGY → ECONOMICS</span></footer>
  </div>
}
