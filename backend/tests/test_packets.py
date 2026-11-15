"""Exercise packet ingestion with temporary databases, never the group demo DB."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.mission import MissionState, TelemetrySample
from app.models.packet import MissionPacket


# Expected checksums were calculated by the crc function in the group's HTML,
# not by the Python validator under test.
PRELAUNCH = {"alt": 0, "vel": 0, "g": 1, "tmp": 24, "pwr": 98, "prs": 310, "seq": 1, "crc": 4421}
ORBIT = {"alt": 408, "vel": 7.66, "g": 0, "tmp": 21, "pwr": 82, "prs": 101.3, "seq": 1, "crc": 13784}
LEGACY_READINGS = {"alt": 408, "vel": 7.66, "cab": 101, "pwr": 82, "tmp": 21, "o2": 94}


class PacketIngestionTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        database_path = Path(directory) / "packets.db"
        self.engine = create_engine(
            URL.create("sqlite", database=str(database_path)),
            connect_args={"check_same_thread": False},
        )
        self.addCleanup(self.engine.dispose)
        self.enterContext(patch("app.main.engine", self.engine))
        self.enterContext(patch("app.main.DATABASE_PATH", database_path))
        self.enterContext(patch(
            "app.database.SessionLocal",
            sessionmaker(bind=self.engine, autoflush=False, autocommit=False),
        ))
        self.enterContext(patch(
            "app.database.engine.connect",
            side_effect=AssertionError("Packet tests must not access the group demo database"),
        ))
        self.client_stack = ExitStack()
        self.addCleanup(self.client_stack.close)
        self.client = self.client_stack.enter_context(TestClient(app))

    def post(self, packet=None, stream="demo-1"):
        return self.client.post(
            f"/api/packet-streams/{stream}/packets",
            json=PRELAUNCH if packet is None else packet,
        )

    def packet_count(self):
        with Session(self.engine) as db:
            return db.scalar(select(func.count()).select_from(MissionPacket))

    def test_valid_browser_packet_is_recorded(self):
        response = self.post()
        self.assertEqual(response.status_code, 201, response.text)
        receipt = response.json()
        self.assertFalse(receipt["duplicate"])
        self.assertEqual(receipt["stream_id"], "demo-1")
        self.assertEqual(receipt["seq"], PRELAUNCH["seq"])
        with Session(self.engine) as db:
            stored = db.get(MissionPacket, receipt["id"])
            self.assertEqual(stored.packet, PRELAUNCH)
            self.assertIsNotNone(stored.recorded_at)

    def test_exact_replay_returns_original_receipt_without_second_row(self):
        first = self.post()
        replay = self.post()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json(), {**first.json(), "duplicate": True})
        self.assertEqual(self.packet_count(), 1)

    def test_duplicate_detection_survives_app_lifespan_and_connection_restart(self):
        first = self.post().json()
        self.client_stack.close()
        self.engine.dispose()
        self.client = self.client_stack.enter_context(TestClient(app))
        replay = self.post()
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json(), {**first, "duplicate": True})
        self.assertEqual(self.packet_count(), 1)

    def test_reusing_sequence_for_changed_valid_packet_returns_conflict(self):
        self.assertEqual(self.post().status_code, 201)
        conflict = self.post(ORBIT)
        self.assertEqual(conflict.status_code, 409, conflict.text)
        self.assertIn("sequence", conflict.json()["detail"])
        self.assertEqual(self.packet_count(), 1)
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(MissionPacket)).packet, PRELAUNCH)

    def test_sequence_numbers_are_scoped_to_each_run(self):
        first = self.post(stream="run-A")
        second = self.post(ORBIT, stream="run-B")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(self.packet_count(), 2)

    def test_out_of_order_packets_are_not_mistaken_for_duplicates(self):
        later = {**PRELAUNCH, "seq": 10, "crc": 4430}
        self.assertEqual(self.post(later).status_code, 201)
        self.assertEqual(self.post(PRELAUNCH).status_code, 201)
        self.assertEqual(self.post(later).status_code, 200)
        self.assertEqual(self.packet_count(), 2)

    def test_corruption_is_rejected_and_does_not_reserve_sequence(self):
        corrupt = {**PRELAUNCH, "tmp": 25}  # Old checksum after a changed reading.
        response = self.post(corrupt)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("checksum", response.text)
        self.assertEqual(self.packet_count(), 0)
        self.assertEqual(self.post().status_code, 201)

    def test_missing_unknown_or_wrongly_typed_values_are_rejected(self):
        missing = dict(PRELAUNCH)
        missing.pop("prs")
        cases = [missing, {**PRELAUNCH, "unknown": 1}, {}, [], None]
        for key, value in (
            ("alt", "0"), ("g", True), ("tmp", None), ("pwr", 101),
            ("pwr", -1), ("alt", -1), ("vel", -1), ("prs", -1),
            ("seq", -1), ("seq", 0.5), ("seq", True), ("seq", "1"),
            ("seq", 2**53), ("crc", 1.5), ("crc", True), ("crc", 65521),
        ):
            cases.append({**PRELAUNCH, key: value})
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post("/api/packet-streams/demo-1/packets", json=payload)
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.packet_count(), 0)

    def test_non_finite_or_overflowing_readings_return_validation_errors(self):
        for token in ("NaN", "Infinity", "-Infinity", "1e999", "1e308"):
            with self.subTest(token=token):
                body = json.dumps(PRELAUNCH).replace('"alt": 0', '"alt": ' + token)
                response = self.client.post(
                    "/api/packet-streams/demo-1/packets", content=body,
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.packet_count(), 0)

    def test_malformed_json_and_invalid_stream_ids_return_validation_errors(self):
        response = self.client.post(
            "/api/packet-streams/demo-1/packets", content="{",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)
        for stream in ("_bad", "bad.name", "x" * 65):
            self.assertEqual(self.post(stream=stream).status_code, 422)
        self.assertEqual(self.packet_count(), 0)

    def test_browser_checksum_rounding_sign_and_wraparound_match(self):
        base = {"alt": 0, "vel": 0, "g": 0, "tmp": 0, "pwr": 0, "prs": 0, "seq": 0, "crc": 0}
        vectors = [
            ORBIT,
            {**base, "tmp": 0.05, "crc": 1},
            {**base, "tmp": -0.05, "crc": 0},
            {**base, "tmp": -0.15, "crc": -1},
            {**base, "seq": 65521, "crc": 0},
            {"alt": 408.23, "vel": 7.65, "g": -0.02, "tmp": -18.75,
             "pwr": 92.31, "prs": 100.12, "seq": 42, "crc": 13509},
        ]
        for index, packet in enumerate(vectors):
            with self.subTest(packet=packet):
                response = self.post(packet, stream=f"vector-{index}")
                self.assertEqual(response.status_code, 201, response.text)

    def test_valid_out_of_alert_range_data_is_still_accepted(self):
        # An unusual temperature is evidence for alerts, not a corrupted packet.
        packet = {**PRELAUNCH, "tmp": 200, "crc": 6181}
        response = self.post(packet)
        self.assertEqual(response.status_code, 201, response.text)

    def test_simultaneous_retries_cannot_create_duplicate_rows(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(pool.map(lambda _: self.post(), range(6)))
        self.assertEqual(sorted(r.status_code for r in responses), [200] * 5 + [201])
        self.assertEqual(len({r.json()["id"] for r in responses}), 1)
        self.assertEqual(self.packet_count(), 1)

    def test_simultaneous_conflicting_packets_do_not_overwrite_each_other(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(self.post, (PRELAUNCH, ORBIT)))
        self.assertEqual(sorted(r.status_code for r in responses), [201, 409])
        self.assertEqual(self.packet_count(), 1)
        winner = (PRELAUNCH, ORBIT)[next(i for i, r in enumerate(responses) if r.status_code == 201)]
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(MissionPacket)).packet, winner)

    def test_new_packet_endpoint_leaves_legacy_mission_state_alone(self):
        saved = self.client.post("/api/telemetry", json={"readings": LEGACY_READINGS})
        self.assertEqual(saved.status_code, 201, saved.text)
        before = self.client.get("/api/dashboard").json()
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.post().status_code, 200)
        after = self.client.get("/api/dashboard").json()
        for key in ("phase", "link", "checks", "metrics", "started_at", "telemetry_updated_at"):
            self.assertEqual(before[key], after[key])
        self.assertEqual(self.client.get("/api/telemetry/latest").json(), saved.json())
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(TelemetrySample)), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(MissionState)), 1)


if __name__ == "__main__":
    unittest.main()
