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

<<<<<<< HEAD
The first dashboard request initializes `backend/app.db` with example telemetry. Telemetry values are simulated by the backend and persisted between requests; the simulated comms dropout holds the last values. When serving the frontend from another local development server, it requests `http://localhost:8000` by default. Set `window.REMNANT_API_BASE` before the dashboard script to use another API origin.

## Inventory API

The repository also contains a standalone inventory API for saved supply quantities, remaining supply days, shortage alerts, and summary counts. See [inventory API setup and examples](backend/README.md).

It runs separately using `app.main:app` on port 8080 with `backend/data/remnant.db`. Its routes are not mounted in the dashboard server described above.

## Automated checks

The mission dashboard checks cover telemetry responses, saved phases and checklist completion, communications dropout and recovery, invalid input, the mission clock, and persistence after restarting the application. They use temporary SQLite databases and block connections to the shared demo database.

The checks send samples through the new telemetry API directly, so the data generator does not need to be running. They also verify that reading the dashboard does not generate samples, incoming data is archived during a dropout, and older telemetry archives upgrade without losing readings.

From the repository root, using your backend Python environment:

```sh
cd backend
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p "test_mission_dashboard.py" -v
```

To run all backend checks, including the separate inventory API:

```sh
python -m unittest discover -s tests -v
```

No running server or browser is needed. A successful run finishes with `OK`; failures show which behavior broke. The normal dashboard command remains `uvicorn main:app --reload`.
=======
FastAPI creates the tables in `backend/app.db` at startup and logs the exact database path. The simulator runs separately and POSTs one sample per second. Each accepted sample is appended to `telemetry_samples`; the table is not truncated. During a simulated comms dropout, samples continue to be stored while the dashboard holds the last values received over the link. When serving the frontend from another local development server, it requests `http://localhost:8000` by default. Set `window.REMNANT_API_BASE` before the dashboard script to use another API origin.
>>>>>>> 66754eedf0583cfd58aeeeb913448903dd2f5db3
