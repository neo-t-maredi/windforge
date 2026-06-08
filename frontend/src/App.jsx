// App.jsx
// WindForge frontend entry point.
// Handles top-level routing between pages:
// SiteSelector → Results Dashboard → Report Export.
// API base URL points to FastAPI backend on port 8000.

import { useState } from "react"

const API_BASE = "http://127.0.0.1:8000"

function App() {
  const [status, setStatus] = useState(null)

  const ping = async () => {
    const res = await fetch(`${API_BASE}/`)
    const data = await res.json()
    setStatus(data.status)
  }

  return (
    <div style={{ fontFamily: "monospace", padding: "2rem" }}>
      <h1>⚡ WindForge</h1>
      <p>Wind site feasibility analysis tool</p>
      <button onClick={ping}>Ping API</button>
      {status && <p style={{ color: "green" }}>✓ {status}</p>}
    </div>
  )
}

export default App