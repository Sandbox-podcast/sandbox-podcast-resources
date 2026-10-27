from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.core import State, comment_needs_human_review, find_new_uploads, parse_reply_decision
from youtube_growth.thumbnails import _fetch_thumbnail, safe_slug, thumbnail_url


class CoreTests(unittest.TestCase):
    def test_new_uploads_are_returned_oldest_first(self) -> None:
        self.assertEqual(find_new_uploads(["newest", "middle", "cursor"], "cursor"), ["middle", "newest"])

    def test_missing_upload_cursor_fails_closed(self) -> None:
        self.assertIsNone(find_new_uploads(["newest", "older"], "missing"))

    def test_first_run_does_not_backfill_channel_history(self) -> None:
        self.assertEqual(find_new_uploads(["newest", "older"], None), [])

    def test_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "state.json"
            state = State(last_video_id="abc", pending_video_ids=["def"], posted_episode_comments=["abc"], seen_comment_ids=["xyz"])
            state.save(path)
            self.assertEqual(State.load(path), state)

    def test_corrupt_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"comments_baselined": "yes"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                State.load(path)

    def test_sensitive_comments_are_routed_to_human(self) -> None:
        self.assertTrue(comment_needs_human_review("J'ai besoin d'un diagnostic médical"))
        self.assertTrue(comment_needs_human_review("Mon mail est contact@example.com"))
        self.assertFalse(comment_needs_human_review("Merci pour cette émission très intéressante !"))

    def test_invalid_ai_output_never_publishes(self) -> None:
        self.assertFalse(parse_reply_decision("voici une réponse").publish)
        self.assertFalse(parse_reply_decision('{"publish": true, "reply": "", "reason": ""}').publish)

    def test_valid_ai_decision_is_trimmed(self) -> None:
        decision = parse_reply_decision('{"publish": true, "reply": "  Merci !  ", "reason": "positif"}')
        self.assertTrue(decision.publish)
        self.assertEqual(decision.reply, "Merci !")

    def test_thumbnail_helpers(self) -> None:
        self.assertEqual(safe_slug("Épisode #1 — IA"), "episode-1-ia")
        self.assertEqual(thumbnail_url({"medium": {"url": "https://i.ytimg.com/vi/abc/mqdefault.jpg"}}), "https://i.ytimg.com/vi/abc/mqdefault.jpg")
        self.assertIsNone(thumbnail_url({}))
        with self.assertRaises(ValueError):
            _fetch_thumbnail("http://example.com/image.png")


if __name__ == "__main__":
    unittest.main()
