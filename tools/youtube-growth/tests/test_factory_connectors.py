from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory.connectors import (ConnectorError, SimulationConnector, SimulationOnlyError,
                                              build_connector, guard_legacy_write)


class FactoryConnectorTests(unittest.TestCase):
    def setUp(self):
        self.config = {"mode": "simulation", "live_enabled": False,
                       "authorized_accounts": {"youtube": ["configured-channel"]}}
        self.publication = {"publication_id": "episode-1:clip-1:youtube", "platform": "youtube",
                            "account_id": "configured-channel"}

    def test_dispatch_never_uses_network_even_with_credentials(self):
        with patch.dict(os.environ, {"YOUTUBE_OAUTH_TOKEN_JSON": "secret", "SANDBOX_FACTORY_MODE": "live"}), \
                patch.object(socket, "socket", side_effect=AssertionError("Network forbidden")):
            connector = build_connector("youtube", "configured-channel", self.config)
            first = connector.dispatch(self.publication)
            second = connector.dispatch(self.publication)
            self.assertEqual(first["status"], "simulated")
            self.assertTrue(first["remote_id"].startswith("sim:youtube:"))
            self.assertEqual(first["remote_id"], second["remote_id"])
            self.assertTrue(second["deduplicated"])
            self.assertFalse(connector.has_remote_transport)
            self.assertEqual(connector.collect(first), [])

    def test_factory_cannot_be_activated_by_configuration(self):
        for setting in ({**self.config, "mode": "live"}, {**self.config, "live_enabled": True}):
            with self.assertRaises(SimulationOnlyError):
                build_connector("youtube", "configured-channel", setting)

    def test_unknown_account_and_destination_are_blocked(self):
        with self.assertRaises(ConnectorError):
            build_connector("youtube", "another-channel", self.config)
        connector = build_connector("youtube", "configured-channel", self.config)
        with self.assertRaises(ConnectorError):
            connector.dispatch({**self.publication, "account_id": "another-channel"})

    def test_linkedin_refuses_all_dispatches(self):
        connector = SimulationConnector("linkedin", "explicit-manual-account")
        with self.assertRaisesRegex(ConnectorError, "linkedin_manual_only"):
            connector.dispatch({"publication_id": "manual-pack"})

    def test_legacy_guard_blocks_all_mutations_and_ignores_environment(self):
        with patch.dict(os.environ, {"SANDBOX_FACTORY_MODE": "live", "YOUTUBE_ALLOW_WRITES": "1"}):
            for action in ("upload", "private_upload", "draft", "schedule", "metadata", "restore", "reply", "delete"):
                with self.assertRaises(SimulationOnlyError):
                    guard_legacy_write(action, config={"mode": "live", "live_enabled": True})

    def test_unknown_after_accept_reconciles_without_second_dispatch(self):
        connector = SimulationConnector("youtube", "configured-channel", scenarios=["unknown_after_accept"])
        with self.assertRaises(ConnectorError) as captured:
            connector.dispatch(self.publication)
        self.assertTrue(captured.exception.uncertain)
        self.assertFalse(captured.exception.retryable)
        receipt = connector.reconcile(self.publication)
        self.assertEqual(receipt["status"], "simulated")
        self.assertTrue(receipt["reconciled"])
        restarted = SimulationConnector("youtube", "configured-channel")
        self.assertEqual(restarted.reconcile(self.publication)["status"], "unknown")
        self.assertEqual(restarted.reconcile({**self.publication, **receipt})["status"], "simulated")

    def test_unknown_result_is_not_marked_safe_for_retry(self):
        connector = SimulationConnector("youtube", "configured-channel", scenarios=["unknown"])
        with self.assertRaises(ConnectorError) as captured:
            connector.dispatch(self.publication)
        self.assertTrue(captured.exception.uncertain)
        self.assertFalse(captured.exception.retryable)
        self.assertEqual(connector.reconcile(self.publication)["status"], "unknown")

    def test_transient_quota_and_expired_token_have_distinct_policies(self):
        connector = SimulationConnector("youtube", "configured-channel", scenarios=["transient", "quota", "expired_token"])
        for retryable, delay in ((True, 60), (True, 3600), (False, None)):
            with self.assertRaises(ConnectorError) as captured:
                connector.dispatch(self.publication)
            self.assertEqual(captured.exception.retryable, retryable)
            self.assertEqual(captured.exception.retry_after_seconds, delay)
            self.assertFalse(captured.exception.uncertain)

    def test_synthetic_metrics_require_explicit_fixture(self):
        connector = build_connector("youtube", "configured-channel", self.config)
        receipt = connector.dispatch(self.publication)
        self.assertEqual(connector.collect(receipt), [])
        rows = connector.collect(receipt, fixture=True, collected_at="2026-10-28T12:00:00+01:00")
        self.assertEqual(rows[0]["data_class"], "synthetic_fixture")
        self.assertEqual(rows[0]["source"], "local_simulation_fixture")
        with self.assertRaises(ConnectorError):
            connector.collect(self.publication, fixture=True)


class HistoricalWriteBarrierTests(unittest.TestCase):
    """Exercise actual entry points, with the factory barrier left unpatched."""

    def test_top_level_comment_is_blocked_before_any_service_method(self):
        from youtube_growth.youtube_api import post_top_level_comment
        service = Mock()
        with self.assertRaises(SimulationOnlyError):
            post_top_level_comment(service, "configured-channel", "abcdefghijk", "Texte local")
        self.assertEqual(service.mock_calls, [])

    def test_reply_is_blocked_before_reading_or_posting_the_parent(self):
        from youtube_growth.youtube_api import post_reply
        service = Mock()
        with self.assertRaises(SimulationOnlyError):
            post_reply(service, "parent-id", "Réponse locale")
        self.assertEqual(service.mock_calls, [])

    def test_metadata_and_restoration_are_blocked_before_network_or_journal(self):
        from youtube_growth.identity import SANDBOX_CHANNEL_ID
        from youtube_growth.operations import execute_plan, make_plan, restoration_plan
        service = Mock()
        plan = make_plan({"id": "abcdefghijk", "snippet": {"channelId": SANDBOX_CHANNEL_ID,
                         "title": "Titre d'origine", "categoryId": "28"}}, {"title": "Titre préparé"})
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "must-not-be-created"
            with patch("youtube_growth.operations.open_journal", side_effect=AssertionError("No journal intent")):
                for candidate in (plan, restoration_plan(plan)):
                    with self.assertRaises(SimulationOnlyError):
                        execute_plan(service, candidate, target, execute=True)
            self.assertFalse(target.exists())
        self.assertEqual(service.mock_calls, [])

    def test_upload_once_is_blocked_before_journal_intent(self):
        from youtube_growth.shorts import upload_once
        service = Mock()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clip.mp4"
            source.write_bytes(b"local fixture")
            with patch("youtube_growth.shorts.open_journal", side_effect=AssertionError("No journal intent")):
                with self.assertRaises(SimulationOnlyError):
                    upload_once(service, source, {"title": "Titre"}, "Épisode", "abcdefghijk")
            self.assertFalse((Path(directory) / "operations.sqlite3").exists())
        self.assertEqual(service.mock_calls, [])

    def test_low_level_private_upload_is_blocked_even_if_called_directly(self):
        from youtube_growth.shorts import _upload_clip
        service = Mock()
        with self.assertRaises(SimulationOnlyError):
            _upload_clip(service, Path("unused-local-file.mp4"), {"title": "Titre"}, "Épisode", "abcdefghijk")
        self.assertEqual(service.mock_calls, [])

    def test_publish_command_is_blocked_before_media_processing(self):
        from youtube_growth.shorts import run
        with patch("youtube_growth.shorts._require_media_tools", side_effect=AssertionError("No media processing")):
            with self.assertRaises(SimulationOnlyError):
                run("unused-local-file.mp4", 1, "fr", "abcdefghijk", True, Path("unused-output"), None)


if __name__ == "__main__":
    unittest.main()
