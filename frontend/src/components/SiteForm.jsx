function Field({ name, label, unit, params, update, min, max, step = 'any' }) {
  return <div className="form-group"><label htmlFor={name}>{label}</label><div className="input-wrap"><input id={name} type="number" required min={min} max={max} step={step} value={params[name]} onChange={e=>update(name,e.target.value)}/><span>{unit}</span></div></div>
}
export default function SiteForm({ params, setParams, onRun, loading }) {
  const update = (key,value) => setParams(prev=>({...prev,[key]:value === '' ? '' : Number(value)}))
  const field = (name,label,unit,min,max) => <Field key={name} {...{name,label,unit,min,max,params,update}}/>
  return <form className="site-form" onSubmit={e=>{e.preventDefault();onRun()}}><fieldset disabled={loading}>
    <section className="form-section"><h3><span>01</span> Site location <small>↗</small></h3><div className="form-row">{field('lat','Latitude','°',-90,90)}{field('lon','Longitude','°',-180,180)}</div><div className="form-row three"><div className="form-group"><label htmlFor="height">Hub height</label><select id="height" value={params.height} onChange={e=>update('height',e.target.value)}>{[50,100,200].map(h=><option key={h} value={h}>{h} m</option>)}</select></div>{field('elevation_m','Elevation','m')}{field('temperature_c','Temperature','°C',-100,100)}</div></section>
    <section className="form-section"><h3><span>02</span> Turbine & terrain <small>↗</small></h3>{field('rated_power_kw','Rated power','kW',1)}<div className="form-group terrain"><label htmlFor="terrain">Terrain complexity</label><select id="terrain" value={params.terrain_complexity} onChange={e=>update('terrain_complexity',e.target.value)}><option value="1">1.00 · Flat / easy access</option><option value="1.15">1.15 · Gentle hills</option><option value="1.3">1.30 · Hilly / ridge</option><option value="1.5">1.50 · Mountainous / remote</option></select><small>Cost multiplier for terrain and access.</small></div></section>
    <section className="form-section"><h3><span>03</span> Cost assumptions <small>↗</small></h3><div className="form-row">{field('capex_per_mw_usd','CAPEX per MW','$',1)}{field('annual_opex_usd','Annual OPEX','$/yr',0)}</div></section>
    <div className="form-submit"><button className="run-btn" type="submit">{loading ? 'Running analysis…' : 'Run analysis'}<span>{loading ? '◌' : '↗'}</span></button><p>All costs in USD · Single-turbine assessment</p></div>
  </fieldset></form>
}
