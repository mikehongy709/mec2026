# RemnantMonitor

RemnantMonitor is a mission telemetry dashboard. FastAPI serves the frontend and stores telemetry, mission phase, communication state and checklist completion in SQLite. A separate Python generator supplies simulated readings.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The backend has one FastAPI app: `app.main:app`. Open <http://localhost:8000>; FastAPI's interactive API page is at <http://localhost:8000/docs>.

Start the telemetry generator in a second terminal so the dashboard receives live readings:

```sh
cd backend
source .venv/bin/activate
python data_generator.py
```

The simulator sends one generated sample per second to FastAPI. It uses only the Python standard library. Set `REMNANT_API_URL` if the API is running at a different base URL; the default is `http://127.0.0.1:8000/api`.

## Dashboard API

The dashboard polls `GET /api/dashboard` once per second. It returns the saved mission phase and clock, communication state, metric readings and histories, phase checklist and completion. Phase, checklist and link controls use the PUT endpoints below and persist their state in SQLite.

| Method | Endpoint | JSON request body |
| --- | --- | --- |
| `GET` | `/api/dashboard` | — |
| `POST` | `/api/telemetry` | `{"readings":{"alt":408.1,"vel":7.66,"cab":101,"pwr":82,"tmp":21,"o2":94}}` |
| `GET` | `/api/telemetry/latest` | — |
| `PUT` | `/api/phase` | `{"phase":"orbit"}` |
| `PUT` | `/api/checklist` | `{"phase":"orbit","item_index":0,"checked":true}` |
| `PUT` | `/api/link` | `{"link":false}` |

The response includes `phase`, `link`, `link_delay_seconds`, `started_at`, `elapsed_seconds`, `metrics`, `checklist_items`, `checks`, and `updated_at`. Each metric has an `id`, display name, unit, current value, alert bounds, simulation step, and 30-value history. Checklist completion is keyed as `<phase>:<item_index>` in `checks`. Unsupported phases, malformed payloads, and checklist indexes outside the selected phase return a validation error.

FastAPI creates the tables in `backend/app.db` at startup and logs the exact database path. The separate Python generator POSTs one sample per second to `telemetry_samples`. The dashboard holds the last displayed readings during a simulated link dropout while incoming samples continue to be archived. It uses the API on its own server, including on non-default ports. When using a separate frontend development server, set `window.REMNANT_API_BASE` before the dashboard script or use `?api=http://localhost:8080` to choose the backend origin. Direct-file previews try the local API on port 8000, then port 8080, accepting only a valid dashboard response.

The additional [packet-validation API](backend/PACKETS.md) remains available for future integrations. The current group dashboard does not call it or require `/api/config` or a WebSocket server.
## Data freshness and validation

If no displayed sample has arrived for more than five seconds, the dashboard marks the readings as stale and keeps the last known values visible. It also marks readings as stale when the simulated link is lost or the API cannot be reached. Before the first sample, it shows a waiting message. Both the backend and Python generator must be running for live readings.

`telemetry_updated_at` is the receive time of the last sample delivered over the link; `telemetry_age_seconds` reports its age, and `telemetry_stale` indicates that it is missing, delayed, or disconnected. `updated_at` remains the time the API response was generated. Samples archived during a simulated dropout do not refresh the displayed readings or receive timestamp.

Battery and oxygen percentages stay between 0 and 100 in generated samples. The API rejects impossible percentages, missing metrics, non-finite numbers, and unexpected fields with HTTP 422. Low but physically valid values still produce the normal threshold alerts.

## Automated checks

From `backend`, using your Python environment:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Backend checks exercise packet validation, duplicate protection and compatibility with the mission API using temporary databases. No running server, browser, or shared demo database is required.

With Node installed, the frontend checks include JavaScript syntax validation to catch unresolved merge markers:

```sh
node --test frontend/tests/*.test.cjs
```

The legacy `uvicorn main:app` entry point is a compatibility alias for the same `app.main:app` application. The separate inventory prototype has been removed.

The database defaults to `backend/app.db`. Set `REMNANT_DB_PATH` to use another SQLite file, for example an isolated local preview. The application logs the selected path on startup.
