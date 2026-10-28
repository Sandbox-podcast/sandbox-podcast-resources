"""Editorial withdrawals and daily limits remain effective until dispatch."""
import hashlib
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from youtube_growth.factory import runtime, scheduler
from youtube_growth.factory.contracts import load_config
from youtube_growth.factory.store import Store

AT = "2026-10-28T17:00:00+01:00"


class EditorialRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = load_config()
        self.config["inbox_directory"] = str(self.root / "inbox")
        self.source = self.root / "source.bin"
        self.source.write_bytes(b"editorial test source")
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.episode = {"version": 1, "episode_id": "editorial-test", "title": "Fixture",
            "source": str(self.source), "source_sha256": self.sha, "synthetic": True,
            "availability": "available", "available_at": "2026-10-27T10:00:00+01:00",
            "availability_checked_at": "2026-10-27T10:00:00+01:00", "availability_evidence": "fixture",
            "full_episode_id": "abcdefghijk", "full_episode_url": "https://www.youtube.com/watch?v=abcdefghijk",
            "next_filming_at": "2026-10-30T18:00:00+01:00"}
        self.store = Store(self.root / "state")
        self.addCleanup(self.store.close)
        self.store.put("episode", self.episode["episode_id"], self.episode, episode_id=self.episode["episode_id"])
        self.candidate = {"segment_id": "segment-one", "episode_id": self.episode["episode_id"],
            "decision": "retained", "title": "Passage", "start_seconds": 0, "end_seconds": 12}
        self.store.put("candidate", "segment-one", self.candidate, episode_id=self.episode["episode_id"])
        self.asset = {"asset_id": "asset-one", "episode_id": self.episode["episode_id"], "path": str(self.source),
            "sha256": self.sha, "qa_status": "passed", "qa": {"technical": "passed"}}
        self.store.put("asset", "asset-one", self.asset, episode_id=self.episode["episode_id"])
        self.publication = {"id": "pub-one", "episode_id": self.episode["episode_id"], "segment_id": "segment-one",
            "asset_id": "asset-one", "asset_sha256": self.sha, "platform": "youtube",
            "account_id": self.config["authorized_accounts"]["youtube"][0], "status": "scheduled",
            "scheduled_at": AT, "qa_status": "passed", "editorial_current": True}
        self.store.save_publication(self.publication)
        self.store.enqueue("dispatch", self.episode["episode_id"], {"publication_id": "pub-one"}, key="dispatch:pub-one", now=AT)

    def test_removed_selection_revokes_scheduled_pack_and_dispatch_job(self):
        with patch("youtube_growth.factory.media.analyze", return_value={"candidates": []}):
            runtime.process(self.store, self.config, self.episode["episode_id"], now=AT)
        row = self.store.publication("pub-one")
        self.assertEqual(row["status"], "blocked")
        self.assertFalse(row["editorial_current"])
        self.assertIsNone(row["scheduled_at"])
        self.assertEqual(self.store.jobs()[0]["status"], "blocked")
        self.assertEqual(scheduler.plan(self.store, self.config, self.episode["episode_id"], now=AT)["scheduled"], 0)
        # An explicit retry cannot bypass the withdrawn editorial decision.
        self.store.retry("dispatch:pub-one", now=AT)
        with self.assertRaisesRegex(ValueError, "editorial_revision_changed"):
            scheduler.assert_sendable(self.store, self.config, self.store.publication("pub-one"), now=AT)

    def test_rejected_selection_blocks_stale_scheduled_copy_before_send(self):
        self.store.put("candidate", "segment-one", {**self.candidate, "decision": "rejected"}, episode_id=self.episode["episode_id"])
        with self.assertRaisesRegex(ValueError, "editorial_selection_not_retained"):
            scheduler.assert_sendable(self.store, self.config, self.publication, now=AT)

    def test_missing_selection_record_blocks_planning_and_send(self):
        self.store.db.execute("DELETE FROM records WHERE kind='candidate' AND id='segment-one'")
        with self.assertRaisesRegex(ValueError, "editorial_selection_not_retained"):
            scheduler.assert_sendable(self.store, self.config, self.publication, now=AT)
        result = scheduler.plan(self.store, self.config, self.episode["episode_id"], now=AT)
        self.assertEqual(result["scheduled"], 0)
        self.assertEqual(self.store.publication("pub-one")["blocked_reason"], "editorial_selection_not_retained")

    def test_ingest_title_change_requires_reprocessing_without_invalidating_media_qa(self):
        manifest = self.root / "episode.ready.json"
        manifest.write_text(json.dumps(self.episode), encoding="utf-8")
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}):
            runtime.ingest(self.store, manifest, now=AT)
            manifest.write_text(json.dumps({**self.episode, "title": "Titre corrigé"}), encoding="utf-8")
            runtime.ingest(self.store, manifest, now=AT)
        row = self.store.publication("pub-one")
        self.assertFalse(row["editorial_current"])
        self.assertEqual(row["qa_status"], "passed")
        with patch("youtube_growth.factory.media.render", side_effect=AssertionError("Stale analysis must not render")):
            with self.assertRaisesRegex(ValueError, "editorial_analysis_revision_changed"):
                runtime.render_candidate(self.store, self.config, self.episode["episode_id"], "segment-one", "vertical", now=AT)

    def test_media_review_does_not_reapprove_withdrawn_editorial_selection(self):
        self.store.save_publication({**self.publication, "editorial_current": False, "status": "blocked"})
        runtime.review(self.store, "asset-one", reviewer="reviewer", evidence="fixture", checks=["visual", "audio", "editorial", "subtitles"], now=AT)
        row = self.store.publication("pub-one")
        self.assertEqual(row["status"], "blocked")
        self.assertFalse(row["editorial_current"])

    def test_actual_daily_sends_are_rechecked_even_without_scheduled_dates(self):
        for index, timestamp in enumerate(("2026-10-28T06:00:00+01:00", "2026-10-28T10:00:00+01:00")):
            self.store.save_publication({**self.publication, "id": f"sent-{index}", "status": "simulated", "scheduled_at": None, "simulated_at": timestamp})
        with self.assertRaisesRegex(ValueError, "daily_limit_replan_required"):
            scheduler.assert_sendable(self.store, self.config, self.publication, now=AT)
        scheduler.plan(self.store, self.config, self.episode["episode_id"], now=AT)
        self.assertTrue(self.store.publication("pub-one")["scheduled_at"].startswith("2026-10-29"))

    def test_worker_records_known_blocker_on_publication_without_dispatch(self):
        with patch("youtube_growth.factory.connectors.build_connector", side_effect=AssertionError("Must not send late")):
            result = runtime.run_once(self.store, self.config, now="2026-10-28T17:30:00+01:00")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.store.publication("pub-one")["status"], "blocked")
        self.assertEqual(self.store.publication("pub-one")["blocked_reason"], "missed_slot_replan_required")
        self.assertEqual(self.store.jobs()[0]["last_error"], "missed_slot_replan_required")

    def test_provider_exception_text_is_not_persisted(self):
        with patch("youtube_growth.factory.runtime.dispatch", side_effect=RuntimeError("secret-provider-token")):
            runtime.run_once(self.store, self.config, now="2026-10-28T17:01:00+01:00")
        self.assertEqual(self.store.publication("pub-one")["blocked_reason"], "RuntimeError")
        self.assertNotIn("secret-provider-token", json.dumps(self.store.jobs()))

    def test_daily_limit_uses_paris_calendar_and_separates_accounts(self):
        self.store.save_publication({**self.publication, "id": "previous-day", "status": "simulated", "simulated_at": "2026-10-27T22:59:00Z"})
        for index in range(3):
            self.store.save_publication({**self.publication, "id": f"other-{index}", "account_id": "other-account", "status": "simulated", "simulated_at": AT})
        scheduler.assert_sendable(self.store, self.config, self.publication, now=AT)

    def test_same_media_in_two_episodes_preserves_both_candidate_and_asset_records(self):
        second = {**self.episode, "episode_id": "second-episode"}
        self.store.put("episode", second["episode_id"], second, episode_id=second["episode_id"])
        analysis = {"candidates": [{k: v for k, v in self.candidate.items() if k != "episode_id"}]}
        with patch("youtube_growth.factory.media.analyze", side_effect=lambda *args, **kwargs: copy.deepcopy(analysis)):
            runtime.process(self.store, self.config, second["episode_id"], now=AT)
            runtime.process(self.store, self.config, second["episode_id"], now=AT)
        candidates = self.store.records("candidate", second["episode_id"])
        self.assertEqual(len(candidates), 1)
        self.assertNotEqual(candidates[0]["segment_id"], self.candidate["segment_id"])
        self.assertEqual(self.store.get("candidate", "segment-one")["episode_id"], self.episode["episode_id"])
        with patch("youtube_growth.factory.media.render", side_effect=lambda *args, **kwargs: {**self.asset, "format": "vertical"}), patch("youtube_growth.factory.packaging.prepare", return_value=[]):
            first = runtime.render_candidate(self.store, self.config, second["episode_id"], candidates[0]["segment_id"], "vertical", now=AT)
            repeated = runtime.render_candidate(self.store, self.config, second["episode_id"], candidates[0]["segment_id"], "vertical", now=AT)
        self.assertEqual(first["asset_id"], repeated["asset_id"])
        self.assertNotEqual(first["asset_id"], "asset-one")
        self.assertEqual(self.store.get("asset", "asset-one")["episode_id"], self.episode["episode_id"])
        self.assertEqual(len(self.store.records("asset")), 2)

    def test_worker_skips_obsolete_render_parameters_after_new_selection(self):
        self.store.db.execute("DELETE FROM jobs")
        self.store.enqueue("render", self.episode["episode_id"], {"segment_id": "segment-one", "format": "horizontal",
            "revision": "obsolete-editorial-revision"}, now=AT)
        with patch("youtube_growth.factory.runtime.render_candidate", side_effect=AssertionError("Obsolete render must not run")):
            result = runtime.run_once(self.store, self.config, now="2026-10-28T17:01:00+01:00")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["kind"], "render")


if __name__ == "__main__":
    unittest.main()
