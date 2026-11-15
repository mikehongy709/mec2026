# RemnantMonitor

RemnantMonitor is a mission telemetry dashboard. The browser simulates mission phases, telemetry, communication failures and checklist commands. FastAPI serves the frontend and validates and archives packets in SQLite before they reach the charts.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The backend has one FastAPI app: `app.main:app`. Open <http://localhost:8000>; FastAPI's interactive API page is at <http://localhost:8000/docs>.

The dashboard runs its own simulator and sends packets to the backend. Each page load starts a new packet stream. Rejected or duplicate packets do not add chart points; packets wait for retry if the backend is unreachable. See [packet validation and integration](backend/PACKETS.md).

## Optional legacy telemetry generator

The older persisted-status API and Python generator remain available independently. They do not drive the current dashboard. To run that generator in a second terminal:

```sh
cd backend
source .venv/bin/activate
python data_generator.py
```

The simulator sends one generated sample per second to FastAPI. It uses only the Python standard library. Set `REMNANT_API_URL` if the API is running at a different base URL; the default is `http://127.0.0.1:8000/api`.

## Legacy dashboard API

The older dashboard operations use JSON under `/api`. `GET /api/dashboard` returns the saved mission phase and clock, communication state, metric readings and histories, phase checklist and completion. The current frontend uses `/api/packet-streams/{stream_id}/packets` instead; its phase and checklist simulation remain local to the page.

| Method | Endpoint | JSON request body |
| --- | --- | --- |
| `GET` | `/api/dashboard` | — |
| `POST` | `/api/telemetry` | `{"readings":{"alt":408.1,"vel":7.66,"cab":101,"pwr":82,"tmp":21,"o2":94}}` |
| `GET` | `/api/telemetry/latest` | — |
| `PUT` | `/api/phase` | `{"phase":"orbit"}` |
| `PUT` | `/api/checklist` | `{"phase":"orbit","item_index":0,"checked":true}` |
| `PUT` | `/api/link` | `{"link":false}` |

The response includes `phase`, `link`, `link_delay_seconds`, `started_at`, `elapsed_seconds`, `metrics`, `checklist_items`, `checks`, and `updated_at`. Each metric has an `id`, display name, unit, current value, alert bounds, simulation step, and 30-value history. Checklist completion is keyed as `<phase>:<item_index>` in `checks`. Unsupported phases, malformed payloads, and checklist indexes outside the selected phase return a validation error.

FastAPI creates the tables in `backend/app.db` at startup and logs the exact database path. On the legacy telemetry path, the separate Python generator POSTs one sample per second to `telemetry_samples`. Its saved status holds the last values received over the simulated link during a dropout. The current dashboard instead queues its own packets for validation and stores accepted packets in `mission_packets`. It uses the API on its own server, including on non-default ports. When using a separate frontend development server, set `window.REMNANT_API_BASE` before the dashboard script to the backend origin. File previews default to `http://localhost:8000`.
## Data freshness and validation

If no validated packet has arrived for more than five seconds, the dashboard marks the readings as stale and keeps the last known values visible. It also marks readings as stale when the simulated link is lost or the packet API cannot be reached. Before the first accepted packet, it shows a waiting message. Start the backend to enable validation; the separate Python generator is not required for this dashboard.

In the legacy status API, `telemetry_updated_at` is the receive time of the last sample delivered over the link; `telemetry_age_seconds` reports its age, and `telemetry_stale` indicates that it is missing, delayed, or disconnected. `updated_at` remains the time the API response was generated. Samples archived through that API during a simulated dropout do not refresh its displayed readings or receive timestamp.

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
