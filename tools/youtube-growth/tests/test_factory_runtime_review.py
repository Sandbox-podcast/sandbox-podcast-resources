"""Independent regression scenarios for persistent state and editorial deadlines."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory import runtime, scheduler
from youtube_growth.factory.connectors import SimulationConnector
from youtube_growth.factory.contracts import instant, load_config
from youtube_growth.factory.store import Store


AT = "2026-10-28T10:00:00+01:00"


class FactoryRuntimeIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.config = load_config()
        self.config["inbox_directory"] = str(self.directory / "inbox")
        self.config["authorized_accounts"]["youtube"] = ["configured-channel"]
        self.config["runtime"]["lease_seconds"] = 10
        self.source = self.directory / "source.bin"
        self.source.write_bytes(b"source for deterministic state checks")
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.episode = {"version": 1, "episode_id": "review-fixture", "title": "Fixture des états persistants",
                        "source": str(self.source), "source_sha256": self.sha, "timezone": "Europe/Paris",
                        "availability": "available", "available_at": "2026-10-27T12:00:00+01:00",
                        "availability_checked_at": "2026-10-27T12:00:00+01:00",
                        "availability_evidence": "synthetic test fixture", "full_episode_id": "abcdefghijk",
                        "full_episode_url": "https://www.youtube.com/watch?v=abcdefghijk",
                        "next_filming_at": "2026-10-30T10:00:00+01:00", "synthetic": True}

    def tearDown(self):
        self.temporary.cleanup()

    def seed(self, store, *, publication_id="publication-1", status="scheduled", scheduled_at=AT):
        store.put("episode", self.episode["episode_id"], self.episode,
                  episode_id=self.episode["episode_id"], now=AT)
        asset = {"asset_id": "asset-1", "episode_id": self.episode["episode_id"], "path": str(self.source),
                 "sha256": self.sha, "qa_status": "passed", "qa": {"technical": "passed"}}
        store.put("asset", "asset-1", asset, episode_id=self.episode["episode_id"], now=AT)
        publication = {"id": publication_id, "episode_id": self.episode["episode_id"], "platform": "youtube",
                       "account_id": "configured-channel", "asset_id": "asset-1", "asset_sha256": self.sha,
                       "qa_status": "passed", "status": status, "scheduled_at": scheduled_at, "synthetic": True}
        store.save_publication(publication, now=AT)
        return publication

    def test_duplicate_ready_manifest_produces_one_cycle_and_incomplete_copy_is_blocked(self):
        manifest = self.directory / "episode.ready.json"
        manifest.write_text(json.dumps(self.episode), encoding="utf-8")
        with Store(self.directory / "state") as store, patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}) as probe:
            self.assertEqual(runtime.ingest(store, manifest, now=AT)["status"], "ingested")
            self.assertEqual(runtime.ingest(store, manifest, now=AT)["status"], "duplicate_ignored")
            self.assertEqual(len(store.jobs()), 1)
            self.assertEqual(len(store.records("episode_revision")), 1)
            wrong = {**self.episode, "episode_id": "incomplete", "source_sha256": "0" * 64}
            manifest.write_text(json.dumps(wrong), encoding="utf-8")
            with self.assertRaises(ValueError):
                runtime.ingest(store, manifest, now=AT)
            self.assertIsNone(store.get("episode", "incomplete"))
            self.assertEqual(len(store.jobs()), 1)
            self.assertEqual(probe.call_count, 1)  # Identical ready events reuse the verified probe.

    def test_reservation_is_atomic_between_workers(self):
        state = self.directory / "state"
        with Store(state) as store:
            store.enqueue("process", "episode", {}, now=AT)
        def reserve(_):
            with Store(state) as worker:
                return worker.reserve(now=AT)
        with ThreadPoolExecutor(max_workers=2) as pool:
            reservations = list(pool.map(reserve, range(2)))
        self.assertEqual(sum(item is not None for item in reservations), 1)
        with Store(state) as store:
            self.assertEqual(store.jobs()[0]["attempts"], 1)

    def test_local_work_resumes_after_restart_but_dispatch_intent_becomes_unknown(self):
        state = self.directory / "state"
        with Store(state) as store:
            self.seed(store)
            identity = store.enqueue("dispatch", self.episode["episode_id"], {"publication_id": "publication-1"}, now=AT)
            original = store.reserve(now=AT, lease_seconds=10)
            row = store.publication("publication-1")
            row["status"] = "sending"
            store.save_publication(row, now=AT)
        with Store(state) as restarted:
            self.assertIsNone(restarted.reserve(now="2026-10-28T10:00:11+01:00"))
            self.assertEqual(restarted.publication("publication-1")["status"], "unknown")
            self.assertEqual(restarted.jobs()[0]["status"], "unknown")
            with self.assertRaises(ValueError):
                restarted.retry(identity, now=AT)
            with self.assertRaises(RuntimeError):
                restarted.finish(original)
            local = restarted.enqueue("process", "another-episode", {}, now=AT)
            restarted.reserve(now=AT, lease_seconds=10)
        with Store(state) as restarted:
            retried = restarted.reserve(now="2026-10-28T10:00:11+01:00", lease_seconds=10)
            self.assertEqual(retried["id"], local)
            self.assertEqual(retried["attempts"], 2)

    def test_autumn_and_spring_clock_changes_have_no_duplicate_or_nonexistent_slot(self):
        autumn = list(scheduler.local_slots(instant("2026-10-24T00:00:00Z"), instant("2026-10-27T00:00:00Z"), ["02:30"]))
        self.assertEqual([item.isoformat() for item in autumn],
                         ["2026-10-24T00:30:00+00:00", "2026-10-25T00:30:00+00:00", "2026-10-26T01:30:00+00:00"])
        spring = list(scheduler.local_slots(instant("2026-03-28T00:00:00Z"), instant("2026-03-31T00:00:00Z"), ["02:30"]))
        self.assertEqual([item.isoformat() for item in spring],
                         ["2026-03-28T01:30:00+00:00", "2026-03-30T00:30:00+00:00"])

    def test_cycle_closes_without_new_episode_and_preserves_collect_and_experiment_jobs(self):
        with Store(self.directory / "state") as store:
            self.seed(store)
            store.enqueue("dispatch", self.episode["episode_id"], {"publication_id": "publication-1"}, now=AT)
            store.enqueue("collect", self.episode["episode_id"], {}, now=AT)
            store.put("experiment", "experiment-1", {"experiment_id": "experiment-1", "status": "active"},
                      episode_id=self.episode["episode_id"], now=AT)
            self.assertEqual(scheduler.close_cycles(store, self.config, now="2026-10-30T09:00:00+01:00"), [self.episode["episode_id"]])
            self.assertEqual(store.publication("publication-1")["status"], "expired")
            jobs = {job["kind"]: job["status"] for job in store.jobs()}
            self.assertEqual(jobs, {"dispatch": "expired", "collect": "queued"})
            self.assertEqual(store.get("experiment", "experiment-1")["status"], "active")
            self.assertEqual(scheduler.close_cycles(store, self.config, now="2026-10-30T11:00:00+01:00"), [])

    def test_revoked_availability_and_changed_render_are_rechecked_before_send(self):
        with Store(self.directory / "state") as store:
            publication = self.seed(store)
            scheduler.assert_sendable(store, self.config, publication, now=AT)
            store.put("episode", self.episode["episode_id"], {**self.episode, "availability": "unavailable"}, now=AT)
            with self.assertRaisesRegex(ValueError, "full_episode_not_available"):
                scheduler.assert_sendable(store, self.config, publication, now=AT)
            store.put("episode", self.episode["episode_id"], self.episode, now=AT)
            self.source.write_bytes(b"changed render after approval")
            with self.assertRaisesRegex(ValueError, "asset_file_changed"):
                scheduler.assert_sendable(store, self.config, publication, now=AT)

    def test_unknown_connector_result_is_never_automatically_resent(self):
        state = self.directory / "state"
        with Store(state) as store:
            self.seed(store)
            store.enqueue("dispatch", self.episode["episode_id"], {"publication_id": "publication-1"}, now=AT)
            connector = SimulationConnector("youtube", "configured-channel", scenarios=["unknown_after_accept"])
            with patch("youtube_growth.factory.connectors.build_connector", return_value=connector):
                first = runtime.run_once(store, self.config, now=AT)
            self.assertEqual(first["status"], "unknown")
            self.assertEqual(store.publication("publication-1")["status"], "unknown")
        with Store(state) as store, patch("youtube_growth.factory.connectors.build_connector", side_effect=AssertionError("No redispatch")):
            # Other periodic jobs can execute, but the uncertain dispatch cannot.
            for _ in range(3):
                runtime.run_once(store, self.config, now="2026-10-28T10:00:20+01:00")
            self.assertEqual(store.publication("publication-1")["status"], "unknown")
            self.assertEqual(sum(job["attempts"] for job in store.jobs() if job["kind"] == "dispatch"), 1)

    def test_failed_asset_job_does_not_stop_an_independent_asset(self):
        with Store(self.directory / "state") as store:
            first = store.enqueue("render", "episode", {"segment_id": "bad", "format": "vertical"}, key="a-bad", now=AT)
            second = store.enqueue("render", "episode", {"segment_id": "good", "format": "vertical"}, key="b-good", now=AT)
            def render(*_, **__):
                if _[3] == "bad":
                    raise ValueError("Fixture de candidat invalide.")
                return {"status": "rendered"}
            with patch("youtube_growth.factory.runtime.render_candidate", side_effect=render):
                self.assertEqual(runtime.run_once(store, self.config, now=AT)["status"], "blocked")
                self.assertEqual(runtime.run_once(store, self.config, now=AT)["status"], "completed")
            states = {job["id"]: job["status"] for job in store.jobs()}
            self.assertEqual(states[first], "blocked")
            self.assertEqual(states[second], "completed")

    def test_delayed_episode_replans_within_remaining_window_and_empty_window_blocks(self):
        with Store(self.directory / "state") as store:
            self.seed(store)
            store.enqueue("dispatch", self.episode["episode_id"], {"publication_id": "publication-1"},
                          key="dispatch:publication-1", now=AT)
            delayed = {**self.episode, "available_at": "2026-10-29T13:00:00+01:00"}
            store.put("episode", self.episode["episode_id"], delayed, now=AT)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now=AT)
            self.assertEqual(result["scheduled"], 1)
            publication = store.publication("publication-1")
            self.assertEqual(publication["scheduled_at"], "2026-10-29T16:00:00+00:00")
            dispatch = next(job for job in store.jobs() if job["kind"] == "dispatch")
            self.assertEqual(dispatch["due_at"], publication["scheduled_at"])
            store.put("episode", self.episode["episode_id"],
                      {**delayed, "available_at": "2026-10-30T10:00:00+01:00"}, now=AT)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now=AT)
            self.assertEqual(result["scheduled"], 0)
            self.assertEqual(store.publication("publication-1")["status"], "blocked")

    def test_restart_does_not_flush_missed_slots_and_preserves_actual_spacing(self):
        with Store(self.directory / "state") as store:
            publication = self.seed(store, scheduled_at=AT)
            with self.assertRaisesRegex(ValueError, "missed_slot_replan_required"):
                scheduler.assert_sendable(store, self.config, publication, now="2026-10-28T12:00:00+01:00")
            old = store.publication("publication-1")
            old.update(status="simulated", simulated_at=AT)
            store.save_publication(old, now=AT)
            due = self.seed(store, publication_id="publication-2", scheduled_at="2026-10-28T12:00:00+01:00")
            with self.assertRaisesRegex(ValueError, "minimum_spacing_replan_required"):
                scheduler.assert_sendable(store, self.config, due, now="2026-10-28T12:00:00+01:00")

    def test_other_uncertain_intent_blocks_same_account_and_pre_send_clock_is_fresh(self):
        with Store(self.directory / "state") as store:
            old = self.seed(store, status="unknown")
            due = self.seed(store, publication_id="publication-2")
            with self.assertRaisesRegex(ValueError, "account_has_uncertain_dispatch"):
                scheduler.assert_sendable(store, self.config, due, now=AT)
            old["status"] = "cancelled"
            store.save_publication(old, now=AT)
            due["scheduled_at"] = "2026-10-30T08:20:00+01:00"
            store.save_publication(due, now=AT)
            connector = SimulationConnector("youtube", "configured-channel")
            with patch.object(connector, "dispatch") as send, patch("youtube_growth.factory.runtime.utcnow", side_effect=[
                    instant("2026-10-30T08:20:00+01:00"), instant("2026-10-30T08:30:00+01:00")]):
                with self.assertRaisesRegex(ValueError, "publication_window_expired_or_not_started"):
                    runtime.dispatch(store, self.config, "publication-2", connector=connector)
            send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
