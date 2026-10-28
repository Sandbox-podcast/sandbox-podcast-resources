from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.audit import analytics_reports, collect_audit
from youtube_growth.editorial import parse_youtube_transcript, prepare_native_pack, weekly_slots
from youtube_growth.identity import SANDBOX_CHANNEL_ID, FIRST_VIDEO_ID, verify_channel, verify_video
from youtube_growth.operations import execute_plan, make_plan, restoration_plan
from youtube_growth.storage import Journal, exclusive_run
from youtube_growth.shorts import _review_hash


def service_fixture():
    channel = {"id": SANDBOX_CHANNEL_ID, "contentDetails": {"relatedPlaylists": {"uploads": "uploads"}}}
    video = {"id": FIRST_VIDEO_ID, "snippet": {"channelId": SANDBOX_CHANNEL_ID, "title": "Titre original", "description": "Description originale", "categoryId": "28", "defaultLanguage": "fr", "defaultAudioLanguage": "fr", "tags": ["SANDBOX"], "thumbnails": {"high": {"url": "https://i.ytimg.com/test.jpg"}}, "publishedAt": "2026-10-12T00:00:00Z"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    service = Mock()
    service.channels.return_value.list.return_value.execute.return_value = {"items": [channel]}
    service.videos.return_value.list.return_value.execute.side_effect = lambda **kw: {"items": [copy.deepcopy(video)]}
    def update(part, body):
        video["snippet"].update(body["snippet"])
        return Mock(execute=Mock(return_value={"id": FIRST_VIDEO_ID}))
    service.videos.return_value.update.side_effect = update
    return service, video


class IdentityTests(unittest.TestCase):
    def test_wrong_oauth_channel_is_rejected(self):
        service, _ = service_fixture()
        service.channels.return_value.list.return_value.execute.return_value = {"items": [{"id": "UC" + "x"*22}]}
        with self.assertRaises(RuntimeError):
            verify_channel(service)

    def test_caller_cannot_override_the_channel_allowlist(self):
        service, _ = service_fixture()
        with self.assertRaises(RuntimeError):
            verify_channel(service, "UC" + "x"*22)
        service.channels.assert_not_called()

    def test_video_readable_but_owned_by_another_channel_is_rejected(self):
        service, video = service_fixture()
        video["snippet"]["channelId"] = "UC" + "x"*22
        with self.assertRaises(RuntimeError):
            verify_video(service, FIRST_VIDEO_ID)

    def test_ambiguous_channel_list_is_rejected(self):
        service, _ = service_fixture()
        service.channels.return_value.list.return_value.execute.return_value = {"items": [{"id": SANDBOX_CHANNEL_ID}]*2}
        with self.assertRaises(RuntimeError):
            verify_channel(service)


class MutationTests(unittest.TestCase):
    def setUp(self):
        # Test the historical journal with an entirely mocked YouTube client.
        # The production barrier is tested without a patch in test_factory_connectors.
        self.enterContext(patch("youtube_growth.factory.connectors.guard_legacy_write"))
        self.enterContext(patch.dict(os.environ, {
            "GITHUB_ACTIONS": "false", "YOUTUBE_JOURNAL_DATABASE_URL": "",
        }))
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.service, self.video = service_fixture()
        self.plan = make_plan(self.video, {"title": "Titre plus précis"})

    def test_github_actions_mutation_requires_remote_journal(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with self.assertRaisesRegex(RuntimeError, "YOUTUBE_JOURNAL_DATABASE_URL"):
                execute_plan(self.service, self.plan, self.path, True)
        self.service.videos.return_value.update.assert_not_called()
        self.assertFalse((self.path / "operations.sqlite3").exists())

    def test_dry_run_never_mutates_remote_state(self):
        self.assertEqual(execute_plan(self.service, self.plan, self.path)["status"], "dry_run")
        self.service.videos.return_value.update.assert_not_called()
        self.assertFalse((self.path / "operations.sqlite3").exists())

    def test_edit_preserves_writable_properties_and_ignores_readonly_ones(self):
        result = execute_plan(self.service, self.plan, self.path, True)
        self.assertEqual(result["status"], "applied")
        request = self.service.videos.return_value.update.call_args.kwargs
        self.assertEqual(request["part"], "snippet")
        self.assertEqual(request["body"]["snippet"]["tags"], ["SANDBOX"])
        self.assertEqual(request["body"]["snippet"]["categoryId"], "28")
        self.assertEqual(request["body"]["snippet"]["defaultAudioLanguage"], "fr")
        self.assertNotIn("channelId", request["body"]["snippet"])
        self.assertNotIn("status", request["body"])
        self.assertEqual(len(list((self.path / "backups").glob("*.json"))), 1)

    def test_reexecution_is_a_noop_after_success(self):
        execute_plan(self.service, self.plan, self.path, True)
        self.assertEqual(execute_plan(self.service, self.plan, self.path, True)["status"], "already_applied")
        self.assertEqual(self.service.videos.return_value.update.call_count, 1)

    def test_fresh_plan_can_reapply_an_optimization_after_restoration(self):
        execute_plan(self.service, self.plan, self.path, True)
        execute_plan(self.service, restoration_plan(self.plan), self.path, True)
        fresh = make_plan(self.video, {"title": "Titre plus précis"})
        self.assertEqual(execute_plan(self.service, fresh, self.path, True)["status"], "applied")
        self.assertEqual(self.service.videos.return_value.update.call_count, 3)

    def test_concurrent_editorial_change_is_not_overwritten(self):
        self.video["snippet"]["description"] = "Modification faite par Lou"
        with self.assertRaises(RuntimeError):
            execute_plan(self.service, self.plan, self.path, True)
        self.service.videos.return_value.update.assert_not_called()

    def test_invalid_plan_cannot_alter_category(self):
        self.plan["after"]["categoryId"] = "22"
        with self.assertRaises(ValueError):
            execute_plan(self.service, self.plan, self.path, True)
        self.service.videos.return_value.update.assert_not_called()

    def test_restoration_recovers_previous_metadata(self):
        original = copy.deepcopy(self.video)
        execute_plan(self.service, self.plan, self.path, True)
        execute_plan(self.service, restoration_plan(self.plan), self.path, True)
        self.assertEqual(self.video, original)

    def test_timeout_after_server_commit_does_not_duplicate_mutation(self):
        def timeout(part, body):
            self.video["snippet"].update(body["snippet"])
            raise TimeoutError("Réponse perdue")
        self.service.videos.return_value.update.side_effect = timeout
        with self.assertRaises(TimeoutError):
            execute_plan(self.service, self.plan, self.path, True)
        self.assertEqual(execute_plan(self.service, self.plan, self.path, True)["status"], "already_applied")
        self.assertEqual(self.service.videos.return_value.update.call_count, 1)
        journal = Journal(self.path / "operations.sqlite3")
        try:
            self.assertEqual(journal.entries()[0]["status"], "complete")
        finally:
            journal.close()

    def test_timeout_before_commit_requires_manual_reconciliation(self):
        self.service.videos.return_value.update.side_effect = TimeoutError("Requête incertaine")
        with self.assertRaises(TimeoutError):
            execute_plan(self.service, self.plan, self.path, True)
        with self.assertRaises(RuntimeError):
            execute_plan(self.service, self.plan, self.path, True)
        self.assertEqual(self.service.videos.return_value.update.call_count, 1)

    def test_overlapping_local_runs_are_rejected(self):
        with exclusive_run(self.path):
            with self.assertRaises(RuntimeError):
                with exclusive_run(self.path):
                    self.fail("Deux écritures concurrentes")


class EditorialTests(unittest.TestCase):
    def test_transcript_checks_video_identity_and_merges_duplicate_timestamps(self):
        text = f"Video ID: {FIRST_VIDEO_ID}\n[0:00] Bonjour\n[0:00] à tous\n[0:10] Le modèle ne suffit pas."
        rows = parse_youtube_transcript(text, FIRST_VIDEO_ID, 40)
        self.assertEqual(rows[0], {"start": 0.0, "end": 10.0, "text": "Bonjour à tous", "end_inferred": True})
        with self.assertRaises(ValueError):
            parse_youtube_transcript(text, "aaaaaaaaaaa", 40)

    def test_invalid_timestamps_are_rejected(self):
        for text in ("[0:80] non", "[0:10] a\n[0:02] b", "[1:00] trop loin"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_youtube_transcript(f"Video ID: {FIRST_VIDEO_ID}\n{text}", FIRST_VIDEO_ID, 40)

    def test_native_pack_is_never_marked_published(self):
        rows = [{"start": 0, "end": 60, "text": "Un extrait"}]
        spec = {"video_id": FIRST_VIDEO_ID, "candidates": [{"start": 0, "end": 40, "title": "Un sujet", "reason": "Passage autonome", "selected": True}]}
        pack = prepare_native_pack(rows, spec, FIRST_VIDEO_ID, 100, datetime.fromisoformat("2026-10-15T17:00:00+02:00"))
        self.assertIsNone(pack["candidates"][0]["published_url"])
        self.assertEqual(pack["candidates"][0]["status"], "identified")
        self.assertFalse(pack["transcription_reviewed"])

    def test_native_ranges_reject_nan_overlap_and_long_clips(self):
        rows = [{"start": 0, "end": 100, "text": "Un extrait"}]
        base = {"start": 0, "end": 40, "title": "Un sujet", "reason": "Motif", "selected": True}
        for candidates in ([{**base, "start": float("nan")}], [{**base, "end": 61}], [base, {**base, "start": 20, "end": 50}]):
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                prepare_native_pack(rows, {"video_id": FIRST_VIDEO_ID, "candidates": candidates}, FIRST_VIDEO_ID, 100, datetime.fromisoformat("2026-10-15T17:00:00+02:00"))

    def test_three_weekly_slots_keep_local_time_across_dst(self):
        times = weekly_slots(datetime.fromisoformat("2026-10-23T17:00:00+02:00"), 4)
        self.assertEqual(times, ["2026-10-23T15:00:00Z", "2026-10-25T16:00:00Z", "2026-10-27T16:00:00Z", "2026-10-30T16:00:00Z"])

    def test_approval_is_bound_to_content_but_survives_schedule_updates(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            path = Path(name)
            (path / "clip.mp4").write_bytes(b"media fixture")
            manifest = {"source_sha256": "source", "source_video_id": FIRST_VIDEO_ID, "segments": [], "clips": [{"start": 0, "end": 30, "title": "Sujet", "file": "clip.mp4"}]}
            reviewed = _review_hash(manifest, path)
            manifest["clips"][0].update({"publish_at": "2026-10-15T15:00:00Z", "youtube_video_id": "aaaaaaaaaaa"})
            self.assertEqual(_review_hash(manifest, path), reviewed)
            (path / "clip.mp4").write_bytes(b"media changed")
            self.assertNotEqual(_review_hash(manifest, path), reviewed)


class AnalyticsTests(unittest.TestCase):
    def test_empty_report_is_not_fabricated_zero(self):
        service = Mock()
        service.reports.return_value.query.return_value.execute.return_value = {"columnHeaders": [{"name": "views"}], "rows": []}
        result = analytics_reports(service, SANDBOX_CHANNEL_ID, FIRST_VIDEO_ID, date(2026, 10, 12), date(2026, 10, 13))
        self.assertEqual(result["video_daily"]["status"], "no_data")
        self.assertIsNone(result["studio_only"]["thumbnail_ctr"])

    def test_denied_report_is_explicitly_unavailable(self):
        service = Mock()
        class ApiError(Exception):
            resp = SimpleNamespace(status=403)
        service.reports.return_value.query.return_value.execute.side_effect = ApiError()
        result = analytics_reports(service, SANDBOX_CHANNEL_ID, FIRST_VIDEO_ID, date(2026, 10, 12), date(2026, 10, 13))
        self.assertEqual(result["retention"]["status"], "unavailable")
        self.assertIsNone(result["retention"]["data"])

    def test_malformed_analytics_rows_fail_validation(self):
        service = Mock()
        service.reports.return_value.query.return_value.execute.return_value = {"columnHeaders": [{"name": "views"}], "rows": [[1, 2]]}
        with self.assertRaises(ValueError):
            analytics_reports(service, SANDBOX_CHANNEL_ID, FIRST_VIDEO_ID, date(2026, 10, 12), date(2026, 10, 13))


if __name__ == "__main__":
    unittest.main()
