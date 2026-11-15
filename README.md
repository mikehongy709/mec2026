# RemnantMonitor

RemnantMonitor is a mission telemetry dashboard. FastAPI serves the frontend and a JSON API; telemetry, mission phase, comms-link state, and checklist completion are stored in SQLite.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open <http://localhost:8000>. FastAPI's interactive API page is at <http://localhost:8000/docs>.

## Dashboard API

All dashboard operations use JSON under `/api`. `GET /api/dashboard` returns the current mission phase and clock, communication state, metric readings and histories, the checklist for the active phase, and saved checklist completion. The frontend polls this endpoint once per second. The same dashboard response is returned after updates so the page can immediately render the persisted state.

| Method | Endpoint | JSON request body |
| --- | --- | --- |
| `GET` | `/api/dashboard` | — |
| `PUT` | `/api/phase` | `{"phase":"orbit"}` |
| `PUT` | `/api/checklist` | `{"phase":"orbit","item_index":0,"checked":true}` |
| `PUT` | `/api/link` | `{"link":false}` |

The response includes `phase`, `link`, `link_delay_seconds`, `started_at`, `elapsed_seconds`, `metrics`, `checklist_items`, `checks`, and `updated_at`. Each metric has an `id`, display name, unit, current value, alert bounds, simulation step, and 30-value history. Checklist completion is keyed as `<phase>:<item_index>` in `checks`. Unsupported phases, malformed payloads, and checklist indexes outside the selected phase return a validation error.

The first dashboard request initializes `backend/app.db` with example telemetry. Telemetry values are simulated by the backend and persisted between requests; the simulated comms dropout holds the last values. When serving the frontend from another local development server, it requests `http://localhost:8000` by default. Set `window.REMNANT_API_BASE` before the dashboard script to use another API origin.

## Inventory API

The repository also contains a standalone inventory API for saved supply quantities, remaining supply days, shortage alerts, and summary counts. See [inventory API setup and examples](backend/README.md).

It runs separately using `app.main:app` on port 8080 with `backend/data/remnant.db`. Its routes are not mounted in the dashboard server described above.
