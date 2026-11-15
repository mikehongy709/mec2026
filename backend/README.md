# Remnant inventory backend

## Mission telemetry website

The telemetry website and its API use `backend/main.py` and `backend/app.db`. From this directory, run:

```sh
uvicorn main:app --reload --port 8000
```

In another terminal, run `python data_generator.py` from this directory. It posts one telemetry sample per second. Open <http://localhost:8000/docs> to confirm you are using the **RemnantMonitor API**; the tables and samples are stored in `backend/app.db`.

The inventory prototype documented below is a separate FastAPI app. Its `uvicorn app.main:app --app-dir backend` command uses `backend/data/remnant.db` and does not serve the mission telemetry dashboard.

The first backend feature sets a supply's onboard quantity, saves it in SQLite, and returns its remaining supply days and shortage status. It uses the existing FastAPI, SQLAlchemy, and Pydantic dependencies.

## Run locally

Use Python 3.12 or newer. Create a fresh environment on your own operating system; the existing `backend/.venv` was created on macOS and is not portable.

From the repository root, in Windows PowerShell:

```powershell
py -3.12 -m venv backend/.venv-local
./backend/.venv-local/Scripts/python.exe -m pip install -r backend/requirements.txt
./backend/.venv-local/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080
```

On macOS, Linux, or WSL:

```sh
python3 -m venv backend/.venv-local
backend/.venv-local/bin/python -m pip install -r backend/requirements.txt
backend/.venv-local/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080
```

Open **http://127.0.0.1:8080/docs** to try the API, or use the requests below. The server creates `backend/data/remnant.db` on first startup and seeds the eight supplies from the frontend sample mission. Subsequent startups preserve saved quantities. An optional `REMNANT_DB_PATH` environment variable selects another SQLite file.

The Tabler frontend still runs its own sample data. This backend feature can be exercised independently before frontend integration.

## Read a supply

`GET /api/inventory/{supply_id}`

For example, `GET /api/inventory/water` initially returns 192 L, consumed at 24 L per day: **8 days remaining, healthy**.

## Update its quantity

`PATCH /api/inventory/{supply_id}`

Request body:

```json
{"quantity": 48}
```

PowerShell example:

```powershell
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8080/api/inventory/water -ContentType application/json -Body '{"quantity": 48}'
```

Response:

```json
{
  "id": "water",
  "name": "Drinking water",
  "unit": "L",
  "quantity": 48.0,
  "daily_consumption": 24.0,
  "days_remaining": 2.0,
  "status": "critical"
}
```

The quantity is an absolute value, not an increment. A second identical request leaves it at 48 L. Update it to 192 to restore the initial water quantity.

Rules:

- Remaining days = quantity / mission-wide daily consumption. Classification uses the unrounded value.
- **Critical:** 3 days or less, including zero stock.
- **Watch:** more than 3 days and up to 7 days.
- **Healthy:** more than 7 days.
- With zero daily consumption, `days_remaining` is `null` and status is `healthy` (no ongoing depletion).
- Quantity must be a finite JSON number between 0 and 1,000,000, matching the frontend's input limit. Strings, booleans, null, negative values, and extra fields return HTTP 422.
- Unknown supply IDs return HTTP 404. Invalid requests leave the stored quantity unchanged.

## Tests

Install the additional test dependency:

```powershell
./backend/.venv-local/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
$env:PYTHONPATH = 'backend'
./backend/.venv-local/Scripts/python.exe -m unittest discover -s backend/tests -v
```

Alternatively, run test discovery from the `backend` directory with `-s tests`.

For macOS, Linux, or WSL:

```sh
backend/.venv-local/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend backend/.venv-local/bin/python -m unittest discover -s backend/tests -v
```

Tests use temporary SQLite databases, covering the shortage workflow, boundary values, input validation, missing supplies, zero consumption, and persistence across application restarts.
