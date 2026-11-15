METRIC_DEFINITIONS = [
    {"id": "alt", "name": "Altitude", "unit": "km", "value": 408.0, "step": 0.4, "minimum": 395, "maximum": 420},
    {"id": "vel", "name": "Velocity", "unit": "km/s", "value": 7.66, "step": 0.01, "minimum": 7.5, "maximum": 7.8},
    {"id": "cab", "name": "Cabin pressure", "unit": "kPa", "value": 101.0, "step": 0.5, "minimum": 96, "maximum": 104},
    {"id": "pwr", "name": "Battery charge", "unit": "%", "value": 82.0, "step": 1.2, "minimum": 25, "maximum": 100},
    {"id": "tmp", "name": "Hull temperature", "unit": "°C", "value": 21.0, "step": 0.8, "minimum": -10, "maximum": 35},
    {"id": "o2", "name": "Oxygen reserve", "unit": "%", "value": 94.0, "step": 0.3, "minimum": 30, "maximum": 100},
]

METRIC_IDS = frozenset(metric["id"] for metric in METRIC_DEFINITIONS)
PERCENTAGE_METRIC_IDS = frozenset({"pwr", "o2"})
