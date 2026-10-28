"""Worker consumption, evidence invalidation and actionable local briefs."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory import runtime
from youtube_growth.factory.__main__ import main
from youtube_growth.factory.contracts import load_config
from youtube_growth.factory.efficiency import measured, summarize_runs
from youtube_growth.factory.knowledge import knowledge_status
from youtube_growth.factory.media import fingerprint
from youtube_growth.factory.store import Store

AT = "2026-10-28T09:00:00+00:00"


class EfficiencyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = load_config()
        self.config["inbox_directory"] = str(self.root / "inbox")
        self.inbox = Path(self.config["inbox_directory"])
        self.inbox.mkdir()
        self.store = Store(self.root / "state")
        self.addCleanup(self.store.close)
        self.source = self.root / "source.bin"
        self.source.write_bytes(b"synthetic source")
        self.evidence = self.root / "evidence.json"
        self.evidence.write_text('{}', encoding="utf-8")
        self.manifest = self.inbox / "episode.ready.json"
        self.manifest.write_text(json.dumps({"version": 1, "episode_id": "test", "title": "Titre",
                                            "source": str(self.source), "source_sha256": fingerprint(self.source),
                                            "evidence": str(self.evidence), "synthetic": True}), encoding="utf-8")

    def test_watcher_reuses_success_across_restart_and_verifies_again_after_expiry(self):
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}), \
                patch("youtube_growth.factory.media.fingerprint", wraps=fingerprint) as hashing:
            runtime.watch(self.store, self.config, now=AT)
            self.assertEqual(hashing.call_count, 2)
            with Store(self.store.directory) as restarted:
                self.assertEqual(runtime.watch(restarted, self.config, now="2026-10-28T09:59:00+00:00")["unchanged"], 1)
            self.assertEqual(hashing.call_count, 2)
            runtime.watch(self.store, self.config, now="2026-10-28T10:00:00+00:00")
            self.assertEqual(hashing.call_count, 4)
            self.assertEqual(len(self.store.jobs()), 1)

    def test_watcher_reimports_changed_evidence_and_reports_changed_source(self):
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}):
            runtime.watch(self.store, self.config, now=AT)
            self.evidence.write_text('{"review":"updated"}', encoding="utf-8")
            result = runtime.watch(self.store, self.config, now=AT)
            self.assertEqual(result["ingested"][0]["status"], "ingested")
            self.assertEqual(len(self.store.jobs()), 2)
            self.source.write_bytes(b"source changed")
            result = runtime.watch(self.store, self.config, now=AT)
            self.assertEqual(len(result["errors"]), 1)
            self.assertEqual(len(self.store.jobs()), 2)

    def test_missing_optional_evidence_appearing_is_detected(self):
        self.evidence.unlink()
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}):
            runtime.watch(self.store, self.config, now=AT)
            self.evidence.write_text('{}', encoding="utf-8")
            result = runtime.watch(self.store, self.config, now=AT)
            self.assertEqual(result["ingested"][0]["status"], "ingested")

    def test_editorial_changes_do_not_postpone_periodic_source_verification(self):
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}), \
                patch("youtube_growth.factory.media.fingerprint", wraps=fingerprint) as hashing:
            runtime.watch(self.store, self.config, now=AT)
            self.evidence.write_text('{"review":"new"}', encoding="utf-8")
            runtime.watch(self.store, self.config, now="2026-10-28T09:59:00+00:00")
            self.assertEqual(hashing.call_count, 3)  # Only evidence rehashed.
            runtime.watch(self.store, self.config, now="2026-10-28T10:00:00+00:00")
            self.assertEqual(hashing.call_count, 5)  # Source and evidence verified.

    def test_invalid_manifest_does_not_stop_other_ingestion(self):
        (self.inbox / "invalid.ready.json").write_text('{"source": ["wrong"]}', encoding="utf-8")
        with patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}):
            result = runtime.watch(self.store, self.config, now=AT)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["ingested"]), 1)

    def test_idle_backoff_observes_jobs_closure_and_pause(self):
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=1, interval=15, now=AT), 15)
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=9, interval=15, now=AT), 60)
        self.store.enqueue("render", "test", {}, now="2026-10-28T09:00:04+00:00")
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=9, interval=15, now=AT), 4)
        self.store.set_setting("paused", True)
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=9, interval=15, now=AT), 60)
        self.store.put("episode", "test", {"episode_id": "test", "next_filming_at": "2026-10-28T10:00:08+00:00"})
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=9, interval=15, now=AT), 8)

    def test_exhausted_jobs_and_failed_periodic_job_do_not_create_busy_polling(self):
        self.store.enqueue("render", "test", {}, now=AT)
        self.store.db.execute("UPDATE jobs SET attempts=3")
        self.store.set_setting("last_collection_at", "2026-10-20T09:00:00+00:00")
        self.assertEqual(runtime.idle_delay(self.store, self.config, idle_count=9, interval=15, now=AT), 60)

    def test_stage_measurements_include_failures_and_unknown_energy(self):
        @measured("fixture")
        def successful(store, config, episode_id):
            return {"execution_cache": {"analysis": "hit"}}

        @measured("fixture")
        def failed(store, config, episode_id):
            raise ValueError("secret text must not be stored")

        successful(self.store, self.config, "test")
        with self.assertRaises(ValueError):
            failed(self.store, self.config, "test")
        rows = self.store.records("resource_run", "test")
        summary = summarize_runs(rows)
        self.assertEqual(summary["stages"][0]["runs"], 2)
        self.assertEqual(summary["stages"][0]["failed"], 1)
        self.assertEqual(summary["stages"][0]["cache"]["analysis"]["hits"], 1)
        self.assertNotIn("secret text", json.dumps(rows))
        self.assertIsNone(summary["energy_kwh"])
        self.assertIsNone(summary["monetary_cost"])
        self.assertEqual(summarize_runs([])["stages"], [])

    def test_knowledge_expiry_and_future_reference_are_visible(self):
        self.assertFalse(knowledge_status(self.config, now=AT)["review_required"])
        expired = knowledge_status(self.config, now="2027-02-01T00:00:00+00:00")
        self.assertTrue(expired["review_required"])
        self.assertTrue(all(e["status"] == "review_due" for e in expired["entries"]))
        future = knowledge_status(self.config, now="2025-01-01T00:00:00+00:00")
        self.assertTrue(all(e["status"] == "future_reference" for e in future["entries"]))

    def test_brief_is_read_only_and_does_not_call_a_model(self):
        result = runtime.brief(self.store, self.config, now=AT)
        self.assertFalse(result["policy"]["automatic_strategy_change"])
        self.assertEqual(result["learning"]["facts"], [])
        self.assertEqual(self.store.jobs(), [])
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)

    def test_learning_cannot_move_storage_or_apply_fixtures_through_custom_config(self):
        from youtube_growth.factory.analytics import make_decision
        for field in ("state_directory", "inbox_directory"):
            with self.assertRaises(ValueError):
                make_decision(self.config, {field: ".local/another-state"}, reason="Test",
                              observation_ids=["fixture"], recorded_at=AT, reevaluate_at="2026-11-01T00:00:00+00:00")
        self.store.put("observation", "fixture", {"data_class": "synthetic_fixture"})
        custom_config = self.root / "custom-config.json"
        custom_config.write_text(json.dumps(self.config), encoding="utf-8")
        changes = self.root / "changes.json"
        changes.write_text('{"schedule":{"minimum_spacing_minutes":200}}', encoding="utf-8")
        before = custom_config.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = main(["--config", str(custom_config), "--state-dir", str(self.store.directory),
                         "--now", AT, "decision", "--changes", str(changes), "--reason", "Test",
                         "--reevaluate-at", "2026-11-01T00:00:00+00:00", "--observation-id", "fixture", "--apply"])
        self.assertEqual(code, 2)
        self.assertEqual(custom_config.read_bytes(), before)

    def test_worker_does_not_sleep_between_available_jobs(self):
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps(self.config), encoding="utf-8")
        with patch.object(runtime, "run_once", side_effect=[{"status": "completed"}, {"status": "idle"}, KeyboardInterrupt]), \
                patch("youtube_growth.factory.__main__.time.sleep") as sleep, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                main(["--config", str(config_path), "--state-dir", str(self.root / "worker"), "worker"])
        self.assertEqual(sleep.call_count, 1)
        self.assertEqual(sleep.call_args.args, (15,))


if __name__ == "__main__":
    unittest.main()
