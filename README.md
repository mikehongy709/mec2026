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

Run `main:app` from the `backend` directory for the mission dashboard. `app.main:app` starts a separate inventory prototype and uses a different database. Open <http://localhost:8000>; FastAPI's interactive API page is at <http://localhost:8000/docs>.

In a second terminal, start the simulator:

```sh
cd backend
source .venv/bin/activate
python data_generator.py
```

The simulator sends one generated sample per second to FastAPI. It uses only the Python standard library. Set `REMNANT_API_URL` if the API is running at a different base URL; the default is `http://127.0.0.1:8000/api`.

## Dashboard API

All dashboard operations use JSON under `/api`. `GET /api/dashboard` returns the current mission phase and clock, communication state, metric readings and histories, the checklist for the active phase, and saved checklist completion. The frontend polls this endpoint once per second. The same dashboard response is returned after updates so the page can immediately render the persisted state.

| Method | Endpoint | JSON request body |
| --- | --- | --- |
| `GET` | `/api/dashboard` | — |
| `POST` | `/api/telemetry` | `{"readings":{"alt":408.1,"vel":7.66,"cab":101,"pwr":82,"tmp":21,"o2":94}}` |
| `GET` | `/api/telemetry/latest` | — |
| `PUT` | `/api/phase` | `{"phase":"orbit"}` |
| `PUT` | `/api/checklist` | `{"phase":"orbit","item_index":0,"checked":true}` |
| `PUT` | `/api/link` | `{"link":false}` |

The response includes `phase`, `link`, `link_delay_seconds`, `started_at`, `elapsed_seconds`, `metrics`, `checklist_items`, `checks`, and `updated_at`. Each metric has an `id`, display name, unit, current value, alert bounds, simulation step, and 30-value history. Checklist completion is keyed as `<phase>:<item_index>` in `checks`. Unsupported phases, malformed payloads, and checklist indexes outside the selected phase return a validation error.

The FastAPI server creates the tables in `backend/app.db`. Each accepted simulator request is appended to the `telemetry_samples` table with its timestamp, phase, link state, checklist completion, and metric readings; the archive is not truncated. `GET /api/dashboard` returns the latest readings stored by the server and the 30 most recent values for each sparkline. During a simulated comms dropout, the server continues storing incoming samples while the dashboard holds the last values received over the link. When serving the frontend from another local development server, it requests `http://localhost:8000` by default. Set `window.REMNANT_API_BASE` before the dashboard script to use another API origin.
