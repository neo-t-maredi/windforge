# WindForge UI refresh

## Run in your existing project

Back up your frontend folder, then copy this archive's frontend folder contents over it. Keep your backend as it is.

```bash
cd frontend
npm ci
npm run dev
```

Default backend: http://127.0.0.1:8000. To change it, set VITE_API_BASE_URL in your local .env and restart Vite. Set it before building for deployment. The backend must permit the frontend origin through CORS.

## Preview

Open windforge-preview.html directly in your browser for a self-contained preview. It contains no sample results. Analysis requires the backend; serving via Vite is recommended for API access and CORS.

## Changes

- Responsive assumptions/results layout; light and dark themes.
- Animated SVG turbine rotors, wind traces and orbit; pause and reduced-motion support. The illustration is conceptual, not telemetry.
- Readable labels, explicit units, keyboard focus and input validation.
- Real API health check, HTTP errors, 60-second timeout and changed-input notice.
- Prior results retained if a subsequent request fails.
- All five endpoint paths, query parameters and response fields preserved.
- No added runtime dependencies or backend calculation changes.

## Validation

Production build and ESLint pass. Browser tests could not run: Chromium was unavailable and its download failed. Backend was not included, so live integration and rendered desktop/mobile validation still require local checks.

## Typography refresh

Bundled Latin Modern Sans and Latin Modern Sans Demi Condensed replace the previous Arial/Georgia pairing. Headline emphasis is now upright. Font licenses are included in src/assets/fonts/LICENSE.txt. Layout, colours, animation and application behaviour are unchanged.
