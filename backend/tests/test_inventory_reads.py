"""Verify inventory, alerts, and counts agree as persisted quantities change."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Supply


class InventoryReadTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.application = create_app(Path(directory) / "inventory.db")
        self.client = self.enterContext(TestClient(self.application))

    def test_list_returns_all_supplies_in_stable_order(self):
        response = self.client.get("/api/inventory")
        self.assertEqual(response.status_code, 200)
        supplies = response.json()
        self.assertEqual([supply["id"] for supply in supplies], [
            "batteries", "filters", "food", "fuel", "medical", "oxygen", "parts", "water",
        ])
        self.assertEqual(supplies[-1], {
            "id": "water",
            "name": "Drinking water",
            "unit": "L",
            "quantity": 192,
            "daily_consumption": 24,
            "days_remaining": 8,
            "status": "healthy",
        })

    def test_summary_counts_supplies_and_is_not_captured_as_an_id(self):
        response = self.client.get("/api/inventory/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total_supplies": 8, "healthy": 6, "watch": 1, "critical": 1,
        })

    def test_alerts_include_only_shortages_in_runway_order(self):
        response = self.client.get("/api/alerts")
        self.assertEqual(response.status_code, 200)
        alerts = response.json()
        self.assertEqual([supply["id"] for supply in alerts], ["batteries", "oxygen"])
        self.assertEqual([supply["status"] for supply in alerts], ["critical", "watch"])
        self.assertEqual([supply["days_remaining"] for supply in alerts], [3, 6])

    def test_quantity_changes_immediately_update_all_three_views(self):
        response = self.client.patch("/api/inventory/water", json={"quantity": 48})
        self.assertEqual(response.status_code, 200)
        supplies = self.client.get("/api/inventory").json()
        water = next(supply for supply in supplies if supply["id"] == "water")
        self.assertEqual(water, response.json())
        alerts = self.client.get("/api/alerts").json()
        self.assertEqual([supply["id"] for supply in alerts], ["water", "batteries", "oxygen"])
        self.assertEqual(alerts[0]["days_remaining"], 2)
        self.assertEqual(self.client.get("/api/inventory/summary").json(), {
            "total_supplies": 8, "healthy": 5, "watch": 1, "critical": 2,
        })

        response = self.client.patch("/api/inventory/water", json={"quantity": 192})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([supply["id"] for supply in self.client.get("/api/alerts").json()], ["batteries", "oxygen"])
        self.assertEqual(self.client.get("/api/inventory/summary").json(), {
            "total_supplies": 8, "healthy": 6, "watch": 1, "critical": 1,
        })

    def test_equal_remaining_days_use_id_as_tie_breaker(self):
        response = self.client.patch("/api/inventory/water", json={"quantity": 72})
        self.assertEqual(response.status_code, 200)
        alerts = self.client.get("/api/alerts").json()
        self.assertEqual([supply["id"] for supply in alerts], ["batteries", "water", "oxygen"])
        self.assertEqual([supply["days_remaining"] for supply in alerts], [3, 3, 6])

    def test_zero_consumption_is_counted_as_healthy_and_excluded_from_alerts(self):
        with Session(self.application.state.engine) as session:
            session.add(Supply(id="equipment", name="Reusable equipment", unit="items", quantity=0, daily_consumption=0))
            session.commit()
        supplies = self.client.get("/api/inventory").json()
        equipment = next(supply for supply in supplies if supply["id"] == "equipment")
        self.assertIsNone(equipment["days_remaining"])
        self.assertEqual(equipment["status"], "healthy")
        self.assertNotIn("equipment", [supply["id"] for supply in self.client.get("/api/alerts").json()])
        self.assertEqual(self.client.get("/api/inventory/summary").json(), {
            "total_supplies": 9, "healthy": 7, "watch": 1, "critical": 1,
        })

    def test_empty_inventory_returns_empty_lists_and_zero_counts(self):
        with Session(self.application.state.engine) as session:
            session.execute(delete(Supply))
            session.commit()
        for path in ("/api/inventory", "/api/alerts"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [])
        response = self.client.get("/api/inventory/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total_supplies": 0, "healthy": 0, "watch": 0, "critical": 0,
        })


if __name__ == "__main__":
    unittest.main()
