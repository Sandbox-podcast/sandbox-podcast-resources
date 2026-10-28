"""Operational regressions: revisions, pause and immutable learning evidence."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory import runtime, scheduler
from youtube_growth.factory.__main__ import main
from youtube_growth.factory.contracts import digest, load_config
from youtube_growth.factory.media import fingerprint
from youtube_growth.factory.store import Store

AT = "2026-10-28T09:00:00+00:00"


class FactoryOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = load_config()
        self.config["inbox_directory"] = str(self.root / "inbox")
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.source = self.root / "source.bin"
        self.source.write_bytes(b"source revision one")
        self.evidence = self.root / "evidence.json"
        self.evidence.write_text('{"version":1}', encoding="utf-8")
        self.manifest = self.root / "episode.ready.json"
        self.episode = {"version": 1, "episode_id": "revision-test", "title": "Titre initial", "source": str(self.source),
                        "source_sha256": fingerprint(self.source), "evidence": str(self.evidence),
                        "availability": "available", "available_at": AT, "availability_checked_at": AT,
                        "availability_evidence": "fixture", "full_episode_id": "abcdefghijk",
                        "full_episode_url": "https://www.youtube.com/watch?v=abcdefghijk",
                        "next_filming_at": "2026-10-30T16:00:00+01:00", "synthetic": True}

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.episode), encoding="utf-8")

    def test_title_and_evidence_revisions_reuse_source_probe_but_enqueue_new_processing(self):
        self.write_manifest()
        with Store(self.root / "state") as store, patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}) as probe:
            runtime.ingest(store, self.manifest, now=AT)
            self.episode["title"] = "Titre corrigé"
            self.write_manifest()
            runtime.ingest(store, self.manifest, now=AT)
            self.evidence.write_text('{"version":1,"review":"new"}', encoding="utf-8")
            runtime.ingest(store, self.manifest, now=AT)
            self.assertEqual(probe.call_count, 1)
            self.assertEqual(len(store.jobs()), 3)
            self.assertEqual(len(store.records("episode_revision")), 3)

    def test_new_source_cannot_create_a_second_send_after_an_existing_publication(self):
        self.write_manifest()
        with Store(self.root / "state") as store, patch("youtube_growth.factory.media.probe", return_value={"duration_seconds": 12}):
            runtime.ingest(store, self.manifest, now=AT)
            store.save_publication({"id": "already-done", "episode_id": self.episode["episode_id"], "asset_id": "old",
                                    "platform": "youtube", "account_id": self.config["authorized_accounts"]["youtube"][0], "status": "simulated"}, now=AT)
            self.source.write_bytes(b"revised source with different bytes")
            self.episode["source_sha256"] = fingerprint(self.source)
            self.write_manifest()
            runtime.ingest(store, self.manifest, now=AT)
            current = store.get("episode", self.episode["episode_id"])
            self.assertTrue(current["source_revision_requires_reconciliation"])
            self.assertIn("source_revision_requires_reconciliation", scheduler.plan(store, self.config, self.episode["episode_id"], now=AT)["blocked"])
            self.assertEqual(store.publication("already-done")["status"], "simulated")

    def test_pause_keeps_collections_and_reports_reservable(self):
        with Store(self.root / "state") as store:
            store.enqueue("render", "episode", {}, key="a", now=AT)
            store.enqueue("collect", None, {}, key="b", now=AT)
            store.enqueue("report", None, {}, key="c", now=AT)
            store.set_setting("paused", True)
            first = store.reserve(now=AT)
            self.assertEqual(first["kind"], "collect")
            store.finish(first)
            second = store.reserve(now=AT)
            self.assertEqual(second["kind"], "report")
            store.finish(second)
            self.assertIsNone(store.reserve(now=AT))
            self.assertEqual(store.jobs()[0]["status"], "queued")

    def test_import_rejects_a_conflicting_observation_without_replacing_original(self):
        row = {"observation_id": "obs-1", "platform": "youtube", "account_id": "fixture", "scope": "post", "entity_id": "sim:post", "metric": "views", "value": 12,
               "unit": "count", "statistic": "cumulative", "denominator": None, "source": "fixture", "data_class": "synthetic_fixture",
               "period_start": AT, "period_end": AT, "collected_at": AT, "aggregation_timezone": "Europe/Paris", "definition": "fixture", "definition_version": "v1"}
        path = self.root / "observation.json"
        path.write_text(json.dumps(row), encoding="utf-8")
        args = ["--config", str(self.config_path), "--state-dir", str(self.root / "state"), "record", "--kind", "observation", str(path)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(args), 0)
            row["value"] = 99
            path.write_text(json.dumps(row), encoding="utf-8")
            self.assertEqual(main(args), 2)
        with Store(self.root / "state") as store:
            self.assertEqual(store.get("observation", "obs-1")["value"], 12)

    def test_report_preserves_unmeasured_costs_and_empty_metrics(self):
        with Store(self.root / "state") as store:
            result = runtime.report(store, now=AT, config=self.config)
            self.assertIsNone(result["budget"]["observed"])
            self.assertIsNone(result["budget"]["projected"])
            self.assertEqual(result["metrics"]["series"], [])

    def test_unknown_simulated_result_can_be_reconciled_by_receipt_without_redispatch(self):
        from youtube_growth.factory.connectors import SimulationConnector
        account = self.config["authorized_accounts"]["youtube"][0]
        row = {"id": "unknown-pub", "publication_id": "unknown-pub", "episode_id": "revision-test", "asset_id": "old",
               "platform": "youtube", "account_id": account, "status": "unknown"}
        receipt = SimulationConnector("youtube", account).dispatch(row)
        path = self.root / "receipt.json"
        path.write_text(json.dumps({"publication_id": row["id"], "status": "simulated", "remote_id": receipt["remote_id"], "evidence": "local fixture receipt"}), encoding="utf-8")
        with Store(self.root / "state") as store:
            store.save_publication(row, now=AT)
            store.enqueue("dispatch", row["episode_id"], {"publication_id": row["id"]}, key="dispatch:"+row["id"], now=AT)
            store.db.execute("UPDATE jobs SET status='unknown'")
        args = ["--config", str(self.config_path), "--state-dir", str(self.root / "state"), "reconcile", row["id"], "--receipt", str(path)]
        with contextlib.redirect_stdout(io.StringIO()), patch.object(SimulationConnector, "dispatch", side_effect=AssertionError("Redispatch interdit")):
            self.assertEqual(main(args), 0)
        with Store(self.root / "state") as store:
            self.assertEqual(store.publication(row["id"])["status"], "simulated")
            self.assertEqual(store.jobs()[0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
