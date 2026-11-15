# RemnantMonitor backend

For the separate packet-validation endpoint and duplicate protection, see [PACKETS.md](PACKETS.md). The current dashboard uses the status and telemetry API below.

The backend is one FastAPI application. It stores mission state and incoming telemetry in SQLite at `backend/app.db`.

## Run

From this directory, install dependencies and start the API:

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the Python generator to send live simulated readings:

```sh
python data_generator.py
```

The Python generator sends one sample per second to `/api/telemetry`. The frontend reads `/api/dashboard` and saves phase, checklist and link changes through the PUT endpoints. Use <http://localhost:8000/docs> for the API docs and <http://localhost:8000> for the dashboard.

## API

- `GET /api/dashboard` — current mission status and latest telemetry.
- `POST /api/telemetry` — store one sample from the generator.
- `GET /api/telemetry/latest` — read the newest stored sample.
- `PUT /api/phase` — change the active phase.
- `PUT /api/checklist` — update one checklist item.
- `PUT /api/link` — simulate a link outage or restore it.

remove app.db if you want to restart the demo

```sh
python -m pip install -r requirements.txt
```

