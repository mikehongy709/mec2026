# Remnant inventory backend

The backend lists inventory, reports shortage alerts and summary counts, and saves quantity updates in SQLite. Every response uses the same remaining-day and status calculations. It uses the existing FastAPI, SQLAlchemy, and Pydantic dependencies.

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

This inventory API runs separately from the RemnantMonitor telemetry dashboard and is not connected to that frontend. For the primary dashboard server and its API, follow the [root README](../README.md).

## List inventory

`GET /api/inventory`

Returns a JSON array containing all supplies in ascending ID order. Each entry has the same fields as the single-supply response below: `id`, `name`, `unit`, `quantity`, `daily_consumption`, `days_remaining`, and `status`.

## List shortage alerts

`GET /api/alerts`

Returns a JSON array of supplies marked `critical` or `watch`, ordered by their unrounded `days_remaining` (lowest first), with ID as a tie-breaker. Alerts are calculated from current saved quantities on every request. Replenishing a supply removes it from this list once it becomes healthy.

The initial sample mission returns battery packs (3 days, critical), followed by oxygen (6 days, watch). An empty alert list is `[]`.

## Inventory summary

`GET /api/inventory/summary`

Returns counts of supply records, not combined quantities across different units. With the initial sample data:

```json
{
  "total_supplies": 8,
  "healthy": 6,
  "watch": 1,
  "critical": 1
}
```

An empty inventory returns zero for every count; inventory listing returns `[]`.

To try the new reads from PowerShell while the server is running:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/inventory
Invoke-RestMethod http://127.0.0.1:8080/api/alerts
Invoke-RestMethod http://127.0.0.1:8080/api/inventory/summary
```

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

Tests use temporary SQLite databases, covering the shortage workflow, boundary values, input validation, missing supplies, zero consumption, and persistence across application restarts. They also check listing and alert ordering, summary counts, empty inventory, and all three views updating after quantity changes.
