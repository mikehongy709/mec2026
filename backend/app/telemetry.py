import random


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
    return {
        metric["id"]: previous.get(metric["id"], metric["value"])
        + random.uniform(-metric["step"], metric["step"])
        for metric in METRIC_DEFINITIONS
    }
