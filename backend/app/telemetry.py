METRIC_DEFINITIONS = [
    {"id": "alt", "name": "Altitude", "unit": "km", "value": 408.0, "step": 0.4, "minimum": 396.25, "maximum": 418.75},
    {"id": "vel", "name": "Velocity", "unit": "km/s", "value": 7.66, "step": 0.01, "minimum": 7.515, "maximum": 7.785},
    {"id": "cab", "name": "Cabin pressure", "unit": "kPa", "value": 101.0, "step": 0.5, "minimum": 96.4, "maximum": 103.6},
    {"id": "pwr", "name": "Battery charge", "unit": "%", "value": 82.0, "step": 1.2, "minimum": 28.75, "maximum": 96.25},
    {"id": "tmp", "name": "Hull temperature", "unit": "°C", "value": 21.0, "step": 0.8, "minimum": -7.75, "maximum": 32.75},
    {"id": "o2", "name": "Oxygen reserve", "unit": "%", "value": 94.0, "step": 0.3, "minimum": 33.5, "maximum": 96.5},
]

METRIC_IDS = frozenset(metric["id"] for metric in METRIC_DEFINITIONS)
PERCENTAGE_METRIC_IDS = frozenset({"pwr", "o2"})
