# RemnantMonitor backend

The backend is one FastAPI application. It stores mission state and incoming telemetry in SQLite at `backend/app.db`.

## Run

From this directory, install dependencies and start the API:

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the fake telemetry source:

```sh
python data_generator.py
```

The generator sends one sample per second to FastAPI. The API stores each sample and the dashboard reads the latest persisted state. Use <http://localhost:8000/docs> for the API docs and <http://localhost:8000> for the dashboard.

## API

- `GET /api/dashboard` — current mission status and latest telemetry.
- `POST /api/telemetry` — store one sample from the generator.
- `GET /api/telemetry/latest` — read the newest stored sample.
- `PUT /api/phase` — change the active phase.
- `PUT /api/checklist` — update one checklist item.
- `PUT /api/link` — simulate a link outage or restore it.

The `telemetry_samples` table is append-only and stores each sample with its timestamp and mission status. `mission_state` stores the current dashboard state. Existing SQLite data is kept when the server restarts.
