"""Exercise the inventory workflow against isolated, real SQLite files."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Supply


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = self.enterContext(TemporaryDirectory())
        self.database_path = Path(self.directory) / "inventory.db"
        self.application = create_app(self.database_path)
        self.client = self.enterContext(TestClient(self.application))

    def test_sample_water_starts_healthy(self):
        response = self.client.get("/api/inventory/water")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "id": "water",
            "name": "Drinking water",
            "unit": "L",
            "quantity": 192,
            "daily_consumption": 24,
            "days_remaining": 8,
            "status": "healthy",
        })

    def test_update_flags_shortage_and_saves_quantity(self):
        response = self.client.patch("/api/inventory/water", json={"quantity": 48})
        self.assertEqual(response.status_code, 200)
        supply = response.json()
        self.assertEqual(supply["quantity"], 48)
        self.assertEqual(supply["daily_consumption"], 24)
        self.assertEqual(supply["days_remaining"], 2)
        self.assertEqual(supply["status"], "critical")
        self.assertEqual(self.client.get("/api/inventory/water").json(), supply)
        self.assertEqual(self.client.get("/api/inventory/oxygen").json()["quantity"], 72)

    def test_status_boundaries_zero_and_fractional_quantities(self):
        cases = ((0, "critical"), (72, "critical"), (72.1, "watch"),
                 (168, "watch"), (168.1, "healthy"), (192, "healthy"))
        for quantity, expected_status in cases:
            with self.subTest(quantity=quantity):
                response = self.client.patch("/api/inventory/water", json={"quantity": quantity})
                self.assertEqual(response.status_code, 200)
                self.assertAlmostEqual(response.json()["days_remaining"], quantity / 24)
                self.assertEqual(response.json()["status"], expected_status)

    def test_invalid_quantities_do_not_change_storage(self):
        for quantity in (-1, 1_000_001, None, True, False, "48", "NaN", [], {}):
            with self.subTest(quantity=quantity):
                response = self.client.patch("/api/inventory/water", json={"quantity": quantity})
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/inventory/water").json()["quantity"], 192)

    def test_missing_quantity_and_unknown_fields_are_rejected(self):
        for payload in ({}, {"quantity": 48, "daily_consumption": 1}, {"quantity": 48, "id": "oxygen"}):
            with self.subTest(payload=payload):
                response = self.client.patch("/api/inventory/water", json=payload)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/inventory/water").json()["quantity"], 192)

    def test_non_finite_numbers_are_rejected_with_json_errors(self):
        for token in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(token=token):
                response = self.client.patch(
                    "/api/inventory/water",
                    content='{"quantity": ' + token + '}',
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 422)
                self.assertIn("detail", response.json())
        self.assertEqual(self.client.get("/api/inventory/water").json()["quantity"], 192)

    def test_unknown_supply_returns_not_found(self):
        for method in ("get", "patch"):
            with self.subTest(method=method):
                arguments = {"json": {"quantity": 48}} if method == "patch" else {}
                response = getattr(self.client, method)("/api/inventory/unknown", **arguments)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": "Supply not found"})

    def test_saved_quantity_survives_restart_and_is_not_reseeded(self):
        path = Path(self.directory) / "restart.db"
        with TestClient(create_app(path)) as first_client:
            self.assertEqual(first_client.patch("/api/inventory/water", json={"quantity": 48}).status_code, 200)
        with TestClient(create_app(path)) as restarted_client:
            supply = restarted_client.get("/api/inventory/water").json()
            self.assertEqual(supply["quantity"], 48)
            self.assertEqual(supply["days_remaining"], 2)
            self.assertEqual(supply["status"], "critical")

    def test_zero_consumption_has_no_depletion_date(self):
        with Session(self.application.state.engine) as session:
            session.add(Supply(id="equipment", name="Reusable equipment", unit="items", quantity=5, daily_consumption=0))
            session.commit()
        for quantity in (0, 5):
            with self.subTest(quantity=quantity):
                response = self.client.patch("/api/inventory/equipment", json={"quantity": quantity})
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.json()["days_remaining"])
                self.assertEqual(response.json()["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
