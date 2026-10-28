"""Operational diagnostics distinguish fixture clocks and preserve episode scope."""
from pathlib import Path
import tempfile
import unittest

from youtube_growth.factory.monitoring import enrich, worker_health
from youtube_growth.factory.runtime import status
from youtube_growth.factory.store import Store

NOW = "2026-10-28T12:00:00Z"


class MonitoringTests(unittest.TestCase):
    def test_clock_states_do_not_misrepresent_simulation_as_liveness(self):
        for heartbeat, expected in [
            (None, "missing"),
            ({"clock": "controlled_simulation", "at": NOW}, "simulation"),
            ({"at": "2026-10-28T11:59:30Z"}, "healthy"),
            ({"at": "2026-10-28T11:56:59Z"}, "stale"),
            ({"at": "2026-10-28T12:01:00Z"}, "clock_skew"),
            ({"at": "not-a-date"}, "invalid"),
            ({"at": None}, "invalid"),
            ("bad-state", "invalid"),
        ]:
            with self.subTest(expected=expected):
                self.assertEqual(worker_health(heartbeat, now=NOW)["status"], expected)

    def test_episode_windows_events_and_attention_are_scoped_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary, Store(Path(temporary)) as store:
            for ep in ["a", "b"]:
                store.put("episode", ep, {"episode_id": ep, "synthetic": ep == "a"}, episode_id=ep)
                store.put("window", ep, {"finish_before": ep}, episode_id=ep)
                store.save_publication({"id": "pub-"+ep, "episode_id": ep, "asset_id": ep, "platform": "youtube", "account_id": "sim", "status": "unknown"})
                store.event("publication_event", "pub-"+ep, {})
            store.event("global_event", None, {})
            # More than a page of unrelated events must not hide relevant history.
            for _ in range(60):
                store.event("unrelated", "pub-b", {})
            before = store.db.total_changes
            result = enrich(store, status(store, episode_id="a"), {}, now=NOW)
            self.assertEqual(before, store.db.total_changes)
            self.assertEqual(result["context"]["synthetic_episode_count"], 1)
            self.assertEqual(result["context"]["real_episode_count"], 0)
            self.assertEqual(result["windows"], [{"episode_id": "a", "finish_before": "a"}])
            self.assertEqual([e["entity_id"] for e in result["recent_events"]], [None, "pub-a"])
            self.assertEqual(len(result["attention"]), 1)
            self.assertEqual(result["attention"][0]["severity"], "critical")
            self.assertIn("réconcilier", result["attention"][0]["next_action"])

    def test_empty_store_has_no_false_success_or_attention(self):
        with tempfile.TemporaryDirectory() as temporary, Store(Path(temporary)) as store:
            result = enrich(store, status(store), {}, now=NOW)
            self.assertEqual(result["attention"], [])
            self.assertEqual(result["health"]["worker"]["status"], "missing")
            self.assertEqual(result["windows"], [])


if __name__ == "__main__":
    unittest.main()
