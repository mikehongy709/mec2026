"""Check the group's mission API without reading or writing the demo database."""

from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import Session

from app.models.mission import MissionState
from main import create_app


class MissionDashboardTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.database_path = Path(directory) / "mission-test.db"
        self.engine = self.new_engine(self.database_path)
        self.application = create_app(self.engine)
        # Fail immediately if a test accidentally reaches the shared demo DB.
        self.enterContext(patch(
            "app.core.database.engine.connect",
            side_effect=AssertionError("Mission tests must not connect to backend/app.db"),
        ))
        self.client = self.enterContext(TestClient(self.application))
        # Deterministic readings make recovery/history assertions repeatable.
        self.enterContext(patch("app.services.status_service.random.random", return_value=0.75))

    def new_engine(self, path):
        engine = create_engine(
            URL.create("sqlite", database=str(path)),
            connect_args={"check_same_thread": False},
        )
        self.addCleanup(engine.dispose)
        return engine

    def dashboard(self, client=None):
        response = (client or self.client).get("/api/dashboard")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def update(self, path, payload):
        response = self.client.put(path, json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_dashboard_provides_the_data_the_frontend_needs(self):
        data = self.dashboard()
        self.assertEqual(data["phase"], "orbit")
        self.assertIs(data["link"], True)
        self.assertGreaterEqual(data["elapsed_seconds"], 0)
        self.assertGreaterEqual(data["link_delay_seconds"], 0)
        datetime.fromisoformat(data["started_at"])
        datetime.fromisoformat(data["updated_at"])
        self.assertEqual(data["checks"], {})
        self.assertEqual(len(data["checklist_items"]), 4)
        self.assertTrue(all(isinstance(item, str) and item for item in data["checklist_items"]))
        self.assertEqual({metric["id"] for metric in data["metrics"]}, {"alt", "vel", "cab", "pwr", "tmp", "o2"})
        for metric in data["metrics"]:
            with self.subTest(metric=metric["id"]):
                self.assertTrue(metric["name"])
                self.assertTrue(metric["unit"])
                self.assertTrue(isfinite(metric["value"]))
                self.assertGreater(metric["step"], 0)
                self.assertLess(metric["minimum"], metric["maximum"])
                self.assertEqual(len(metric["history"]), 30)
                self.assertTrue(all(isfinite(value) for value in metric["history"]))
                self.assertEqual(metric["history"][-1], metric["value"])

    def test_frontend_and_api_are_both_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("RemnantMonitor", response.text)
        self.assertEqual(self.client.get("/api/dashboard").status_code, 200)

    def test_every_phase_selects_its_own_checklist_and_is_saved(self):
        checklists = []
        for phase in ("prelaunch", "ascent", "orbit", "reentry"):
            with self.subTest(phase=phase):
                changed = self.update("/api/phase", {"phase": phase})
                self.assertEqual(changed["phase"], phase)
                saved = self.dashboard()
                self.assertEqual(saved["phase"], phase)
                self.assertEqual(saved["checklist_items"], changed["checklist_items"])
                checklists.append(tuple(saved["checklist_items"]))
        self.assertEqual(len(set(checklists)), 4)

    def test_checklist_completion_is_saved_separately_for_each_phase(self):
        self.update("/api/checklist", {"phase": "orbit", "item_index": 0, "checked": True})
        changed = self.update("/api/phase", {"phase": "ascent"})
        self.assertIs(changed["checks"]["orbit:0"], True)
        self.assertFalse(changed["checks"].get("ascent:0", False))
        self.update("/api/checklist", {"phase": "ascent", "item_index": 0, "checked": True})
        self.update("/api/checklist", {"phase": "orbit", "item_index": 0, "checked": False})
        saved = self.dashboard()
        self.assertEqual(saved["phase"], "ascent")
        self.assertIs(saved["checks"]["orbit:0"], False)
        self.assertIs(saved["checks"]["ascent:0"], True)

    def test_dropout_holds_values_and_histories_until_link_recovers(self):
        before = self.dashboard()
        lost = self.update("/api/link", {"link": False})
        self.assertIs(lost["link"], False)
        self.assertEqual(lost["metrics"], before["metrics"])
        for _ in range(3):
            frozen = self.dashboard()
            self.assertIs(frozen["link"], False)
            self.assertEqual(frozen["metrics"], before["metrics"])
        restored = self.update("/api/link", {"link": True})
        self.assertIs(restored["link"], True)
        resumed = self.dashboard()
        self.assertNotEqual(resumed["metrics"], before["metrics"])
        for old, new in zip(before["metrics"], resumed["metrics"]):
            self.assertEqual(new["history"][:-1], old["history"][1:])
            self.assertEqual(new["history"][-1], new["value"])

    def test_ui_settings_do_not_advance_telemetry(self):
        before = self.dashboard()["metrics"]
        changed = self.update("/api/phase", {"phase": "reentry"})
        self.assertEqual(changed["metrics"], before)
        changed = self.update("/api/checklist", {"phase": "reentry", "item_index": 1, "checked": True})
        self.assertEqual(changed["metrics"], before)

    def test_repeated_polling_keeps_history_bounded_and_one_mission_record(self):
        for _ in range(35):
            data = self.dashboard()
            self.assertTrue(all(len(metric["history"]) == 30 for metric in data["metrics"]))
        with Session(self.engine) as session:
            missions = session.scalars(select(MissionState)).all()
            self.assertEqual(len(missions), 1)
            for metric in data["metrics"]:
                self.assertEqual(missions[0].telemetry[metric["id"]]["history"], metric["history"])

    def test_invalid_input_returns_errors_without_changing_mission_state(self):
        self.dashboard()
        baseline = self.update("/api/link", {"link": False})
        cases = (
            ("/api/phase", {"phase": "landing"}),
            ("/api/phase", {"phase": None}),
            ("/api/phase", {}),
            ("/api/checklist", {"phase": "orbit", "item_index": -1, "checked": True}),
            ("/api/checklist", {"phase": "orbit", "item_index": 4, "checked": True}),
            ("/api/checklist", {"phase": "orbit", "item_index": 1.5, "checked": True}),
            ("/api/checklist", {"phase": "unknown", "item_index": 0, "checked": True}),
            ("/api/checklist", {"phase": "orbit", "item_index": 0}),
            ("/api/checklist", {"phase": "orbit", "item_index": 0, "checked": None}),
            ("/api/link", {"link": "invalid"}),
            ("/api/link", {"link": None}),
            ("/api/link", {}),
        )
        for path, payload in cases:
            with self.subTest(path=path, payload=payload):
                response = self.client.put(path, json=payload)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertIn("detail", response.json())
                saved = self.dashboard()
                for key in ("phase", "checks", "link", "started_at", "metrics"):
                    self.assertEqual(saved[key], baseline[key])

    def test_malformed_json_returns_a_clear_error(self):
        response = self.client.put("/api/phase", content="{", headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

    def test_non_finite_checklist_indexes_do_not_crash_the_api(self):
        for token in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(token=token):
                response = self.client.put(
                    "/api/checklist",
                    content='{"phase":"orbit","item_index":' + token + ',"checked":true}',
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 422)
                self.assertIn("detail", response.json())

    def test_mission_clock_uses_the_saved_start_time(self):
        self.dashboard()
        started_at = datetime(2030, 1, 1, 12, 0, 0)
        with Session(self.engine) as session:
            session.get(MissionState, 1).started_at = started_at
            session.commit()
        with patch("app.services.status_service.datetime") as clock:
            clock.utcnow.return_value = started_at + timedelta(seconds=125)
            data = self.dashboard()
        self.assertEqual(data["elapsed_seconds"], 125)
        self.assertEqual(datetime.fromisoformat(data["started_at"]), started_at)

    def test_state_survives_application_restart(self):
        path = Path(self.database_path.parent) / "restart.db"
        with TestClient(create_app(self.new_engine(path))) as first_client:
            self.dashboard(first_client)
            first_client.put("/api/phase", json={"phase": "reentry"}).raise_for_status()
            first_client.put("/api/checklist", json={"phase": "reentry", "item_index": 2, "checked": True}).raise_for_status()
            frozen = first_client.put("/api/link", json={"link": False})
            frozen.raise_for_status()
            before = frozen.json()
        with TestClient(create_app(self.new_engine(path))) as restarted_client:
            saved = self.dashboard(restarted_client)
            self.assertEqual(saved["phase"], "reentry")
            self.assertIs(saved["checks"]["reentry:2"], True)
            self.assertIs(saved["link"], False)
            self.assertEqual(saved["started_at"], before["started_at"])
            self.assertEqual(saved["metrics"], before["metrics"])


if __name__ == "__main__":
    unittest.main()
