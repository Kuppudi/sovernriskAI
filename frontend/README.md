# SovereignRisk AI frontend

React, TypeScript, Vite, and Tailwind.

The first page focuses on ML sovereign risk. Scores stay unavailable until a validated model is connected. Economic indicators are a separate map view and are never presented as risk scores or repayment probabilities.

## Run

From this directory:

```sh
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The development server expects a FastAPI backend at `http://127.0.0.1:8000`. Set `API_PROXY_TARGET` in the repository-root `.env` to change it. For a production build, set `VITE_API_BASE_URL` to the API origin.

```sh
npm run build
npm run preview
```

## Files

- `src/pages/MapExplorer.tsx`: risk and indicator views, country selection.
- `src/components/RiskAssessment.tsx`: model status and unavailable score state.
- `src/components/WorldMap.tsx`: country outlines and map interaction.
- `src/components/CountryPreview.tsx`: selected economic indicator and history.
- `src/hooks/useData.ts`: API queries.
- `src/services/`: requests, labels, and map helpers.

Country outlines are bundled locally; their source is documented in `public/maps/README.md`. The backend is delivered separately from this frontend feature.
