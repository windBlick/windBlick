# WindBlick – frontend

Vue 3 + TypeScript + Vite implementation of the WindBlick Figma prototype
("windblick prototype" file in Figma).

> **Status: prototype for team discussion.** It deviates from `AGENTS.md` in
> two ways that need a team decision: it uses TypeScript, and it contains a
> browser-side projection (`src/lib/projection.ts`) that is only meant as a
> mock until the backend renders visualizations.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # type-check + production build
```

## Flow

| Route      | Screen          | Main pieces                                                    |
|------------|-----------------|----------------------------------------------------------------|
| `/`        | 1. Select photo | `views/UploadView.vue`, EXIF reading in `lib/exif.ts`          |
| `/check`   | 2. Check photo  | `components/check/*` (Leaflet map, camera form, turbine list)  |
| `/preview` | 3. View preview | `components/preview/*` (before/after slider, outline overlay)  |
| —          | Intro pop-up    | `components/intro/*` (4 cards, opened on first visit / "How it works") |

Shared state for all three steps lives in `stores/session.ts` (Pinia).

## Backend / API contract

All backend access goes through `src/api/`. The app currently runs on mocks
(`VITE_USE_MOCKS=true`, see `.env.example`). These provisional functions are
**not yet aligned** with the team contract in `docs/api-contract.md`
(`POST /api/v0/visualizations`, multipart image + JSON parameters, rendering
and EXIF resolution in the backend):

| Function                         | Provisional endpoint        | Mock                                   |
|----------------------------------|-----------------------------|----------------------------------------|
| `getExistingTurbines(bbox)`      | `GET /turbines?bbox=…`      | `api/mocks/nrwTurbines.ts` (GeoJSON)   |
| `generatePreview(request)`       | `POST /preview`             | `lib/projection.ts` (runs in browser)  |

When the contract is available: update the types in `src/types/index.ts` and
the functions in `src/api/` — views and components should not need changes.

Open questions for the backend team:
- Does the backend compute the turbine outlines (`/preview`), or should the
  browser-side projection in `lib/projection.ts` stay?
- Format/CRS of the NRW turbine dataset (GeoJSON in EPSG:4326 assumed).
- Is the photo uploaded at all, or does only the metadata leave the browser?
- Should the downloadable image be rendered by the backend?

## Notes

- The projection is a simple pinhole camera over flat terrain with the rotor
  facing the camera — a geometric approximation, as the UI states.
- Map tiles: OpenStreetMap standard tiles (fine for development; use a proper
  tile provider or the project's WMS for production).
- "Try a sample photo" (upload screen) and "Load sample" (check screen) load a
  bundled illustration with preset camera data for demos.
