
"""Send a fake telemetry sample to FastAPI about once per second."""

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.telemetry import generate_readings, initial_readings


API_BASE = os.environ.get("REMNANT_API_URL", "http://127.0.0.1:8000/api").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 5


def request_json(path: str, *, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{API_BASE}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def load_previous_readings() -> dict[str, float]:
    try:
        sample = request_json("/telemetry/latest")
        return sample["readings"]
    except HTTPError as error:
        if error.code == 404:
            return initial_readings()
        raise


def generate_data() -> None:
    try:
        previous = load_previous_readings()
    except URLError as error:
        print(f"Could not load prior readings; starting from defaults: {error}", file=sys.stderr)
        previous = initial_readings()

    print(f"Sending telemetry to {API_BASE}/telemetry once per second. Press Ctrl+C to stop.")
    while True:
        tick_started = time.monotonic()
        readings = generate_readings(previous)

        while True:
            try:
                sample = request_json("/telemetry", payload={"readings": readings})
                previous = readings
                print(f"Stored sample {sample['id']} at {sample['recorded_at']}", flush=True)
                break
            except (HTTPError, URLError) as error:
                print(f"Telemetry API unavailable; retrying this sample: {error}", file=sys.stderr)
                time.sleep(1)

        time.sleep(max(0, 1 - (time.monotonic() - tick_started)))


if __name__ == "__main__":
    try:
        generate_data()
    except KeyboardInterrupt:
        print("Telemetry generator stopped.")
