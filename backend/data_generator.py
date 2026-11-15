
"""Send a fake telemetry sample to FastAPI about once per second."""

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import random

from app.telemetry import PERCENTAGE_METRIC_IDS


MODE = sys.argv[1] if len(sys.argv) > 1 else "0"
API_BASE = os.environ.get("REMNANT_API_URL", "http://127.0.0.1:8000/api").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 5



METRIC_DEFINITIONS = [
    {"id": "alt", "name": "Altitude", "unit": "km", "value": 408.0, "step": 0.4, "minimum": 395, "maximum": 420},
    {"id": "vel", "name": "Velocity", "unit": "km/s", "value": 7.66, "step": 0.01, "minimum": 7.5, "maximum": 7.8},
    {"id": "cab", "name": "Cabin pressure", "unit": "kPa", "value": 101.0, "step": 0.5, "minimum": 96, "maximum": 104},
    {"id": "pwr", "name": "Battery charge", "unit": "%", "value": 82.0, "step": 1.2, "minimum": 25, "maximum": 100},
    {"id": "tmp", "name": "Hull temperature", "unit": "°C", "value": 21.0, "step": 0.8, "minimum": -10, "maximum": 35},
    {"id": "o2", "name": "Oxygen reserve", "unit": "%", "value": 94.0, "step": 0.3, "minimum": 30, "maximum": 100},
]

METRIC_IDS = frozenset(metric["id"] for metric in METRIC_DEFINITIONS)


def initial_readings() -> dict[str, float]:
    return {metric["id"]: metric["value"] for metric in METRIC_DEFINITIONS}


def generate_readings(previous: dict[str, float]) -> dict[str, float]:
    """Generate one random walk sample from the prior metric values."""
    readings = {
        metric["id"]: previous.get(metric["id"], metric["value"])
        + (random.uniform(-metric["step"], metric["step"]) if MODE == "1" else random.uniform(-5 * metric["step"], 5 * metric["step"]))
        for metric in METRIC_DEFINITIONS
    }
    for metric_id in PERCENTAGE_METRIC_IDS:
        readings[metric_id] = max(0.0, min(100.0, readings[metric_id]))
    return readings


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
