"""The demo generator must produce possible percentages, including at the edges."""

import unittest
from unittest.mock import patch

import data_generator
from app.schemas.mission import TelemetryIngest
from app.telemetry import generate_readings, initial_readings


class TelemetryGeneratorTests(unittest.TestCase):
    def test_positive_drift_stops_at_one_hundred_percent(self):
        previous = {**initial_readings(), "pwr": 99.9, "o2": 99.9}
        with patch("app.telemetry.random.uniform", side_effect=lambda low, high: high):
            for _ in range(10):
                previous = generate_readings(previous)
        self.assertEqual(previous["pwr"], 100)
        self.assertEqual(previous["o2"], 100)

    def test_negative_drift_stops_at_zero_without_hiding_low_supply(self):
        previous = {**initial_readings(), "pwr": 0.1, "o2": 0.1}
        with patch("app.telemetry.random.uniform", side_effect=lambda low, high: low):
            for _ in range(10):
                previous = generate_readings(previous)
        self.assertEqual(previous["pwr"], 0)
        self.assertEqual(previous["o2"], 0)

    def test_restart_with_old_impossible_percentages_recovers_on_next_sample(self):
        previous = {**initial_readings(), "pwr": 106.0, "o2": -2.0, "tmp": -20.0}
        with patch("app.telemetry.random.uniform", return_value=0):
            readings = generate_readings(previous)
        self.assertEqual(readings["pwr"], 100)
        self.assertEqual(readings["o2"], 0)
        self.assertEqual(readings["tmp"], -20)

    def test_script_generator_respects_percentage_bounds_in_both_modes(self):
        for mode in ("0", "1"):
            for edge, direction in ((100, 1), (0, -1)):
                with self.subTest(mode=mode, edge=edge):
                    previous = {**initial_readings(), "pwr": edge, "o2": edge}
                    with patch.object(data_generator, "MODE", mode), patch(
                        "data_generator.random.uniform",
                        side_effect=lambda low, high: high if direction > 0 else low,
                    ):
                        for _ in range(10):
                            previous = data_generator.generate_readings(previous)
                    self.assertEqual(previous["pwr"], edge)
                    self.assertEqual(previous["o2"], edge)

    def test_script_mode_one_uses_normal_steps_and_default_uses_larger_steps(self):
        for mode, scale in (("1", 1), ("0", 5)):
            with self.subTest(mode=mode), patch.object(data_generator, "MODE", mode), patch(
                "data_generator.random.uniform", side_effect=lambda low, high: high,
            ):
                readings = data_generator.generate_readings(initial_readings())
                self.assertAlmostEqual(readings["alt"], 408 + scale * 0.4)

    def test_script_samples_remain_acceptable_to_api_after_invalid_old_percentages(self):
        previous = {**initial_readings(), "pwr": 106, "o2": -2}
        for mode in ("0", "1"):
            with self.subTest(mode=mode), patch.object(data_generator, "MODE", mode):
                readings = data_generator.generate_readings(previous)
                self.assertEqual(TelemetryIngest(readings=readings).readings, readings)


if __name__ == "__main__":
    unittest.main()
