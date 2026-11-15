# RemnantMonitor backend

For the dashboard's simulator packet checks and duplicate protection, see [PACKETS.md](PACKETS.md).

The backend is one FastAPI application. It stores mission state and incoming telemetry in SQLite at `backend/app.db`.

## Run

From this directory, install dependencies and start the API:

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The current dashboard generates its own simulated packets and sends them to the packet-check endpoint before updating charts. It needs the backend running. The Python generator below is optional and feeds the older status API instead:

```sh
python data_generator.py
```

The Python generator sends one sample per second to the older `/api/telemetry` endpoint. Use <http://localhost:8000/docs> for the API docs and <http://localhost:8000> for the current dashboard.

## API

- `GET /api/dashboard` — current mission status and latest telemetry.
- `POST /api/telemetry` — store one sample from the generator.
- `GET /api/telemetry/latest` — read the newest stored sample.
- `PUT /api/phase` — change the active phase.
- `PUT /api/checklist` — update one checklist item.
- `PUT /api/link` — simulate a link outage or restore it.

The `telemetry_samples` table is append-only and stores each sample with its timestamp and mission status. `mission_state` stores the current dashboard state. Existing SQLite data is kept when the server restarts.

## Reliability and checks

Readings are marked stale when the link is lost, the API is unavailable, or the last displayed sample is older than five seconds. Before the first sample the dashboard shows a waiting message. Archived samples received during a simulated dropout do not refresh the displayed timestamp. Battery and oxygen percentages are limited to 0–100; low valid readings still trigger alerts.

Install test dependencies and run the checks from this directory:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Tests check the telemetry generators and API payload validation; they do not modify `app.db`. There is one backend, `app.main:app`; `main:app` is a compatibility alias. To use a different SQLite file, set `REMNANT_DB_PATH` before starting the API.
