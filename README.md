# RemnantMonitor

RemnantMonitor is a mission telemetry dashboard. FastAPI serves the frontend and a JSON API; telemetry, mission phase, comms-link state, and checklist completion are stored in SQLite.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The backend has one FastAPI app: `app.main:app`. Open <http://localhost:8000>; FastAPI's interactive API page is at <http://localhost:8000/docs>.

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

FastAPI creates the tables in `backend/app.db` at startup and logs the exact database path. The simulator runs separately and POSTs one sample per second. Each accepted sample is appended to `telemetry_samples`; the table is not truncated. During a simulated comms dropout, samples continue to be stored while the dashboard holds the last values received over the link. The served dashboard uses the API on its own server, including on non-default ports. When using a separate frontend development server, set `window.REMNANT_API_BASE` before the dashboard script to the backend origin. File previews default to `http://localhost:8000`.
## Data freshness and validation

If no displayed sample has arrived for more than five seconds, the dashboard labels the readings as delayed and keeps the last known values visible. It also marks readings as stale when the link is lost or the API cannot be reached. Before the first sample, it tells the operator to start the generator.

`telemetry_updated_at` is the receive time of the last sample delivered over the link; `telemetry_age_seconds` reports its age, and `telemetry_stale` indicates that it is missing, delayed, or disconnected. `updated_at` remains the time the API response was generated. Samples archived during a simulated dropout do not refresh the displayed readings or their receive timestamp.

Battery and oxygen percentages stay between 0 and 100 in generated samples. The API rejects impossible percentages, missing metrics, non-finite numbers, and unexpected fields with HTTP 422. Low but physically valid values still produce the normal threshold alerts.

## Automated checks

From `backend`, using your Python environment:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Checks exercise both telemetry generators, including their percentage limits, simulation modes, and API payload validation. No running server, browser, or shared demo database is required.

The legacy `uvicorn main:app` entry point is a compatibility alias for the same `app.main:app` application. The separate inventory prototype has been removed.

The database defaults to `backend/app.db`. Set `REMNANT_DB_PATH` to use another SQLite file, for example an isolated local preview. The application logs the selected path on startup.
