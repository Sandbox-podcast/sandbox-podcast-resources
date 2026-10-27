from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.shorts_core import daily_publish_times, format_publish_time, make_srt, next_publish_time, parse_publish_time, validate_clip_candidates


class ShortsCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.segments = [
            {"start": 0.0, "end": 8.0, "text": "Nous discutons de l'intelligence artificielle."},
            {"start": 8.0, "end": 19.5, "text": "La question importante est qui contrôle les données."},
            {"start": 19.5, "end": 32.0, "text": "Il faut regarder les usages avant de parler des outils."},
        ]

    def test_accepts_only_titles_quoted_from_selected_transcript(self) -> None:
        raw = {"clips": [{"start_index": 0, "end_index": 1, "title": "La question importante est"}]}
        clips = validate_clip_candidates(raw, self.segments, 3)
        self.assertEqual(len(clips), 1)
        self.assertEqual(clips[0]["duration"], 19.5)

    def test_rejects_invented_titles_and_out_of_bounds_durations(self) -> None:
        raw = {"clips": [{"start_index": 0, "end_index": 1, "title": "Une invention remarquable"}, {"start_index": 0, "end_index": 0, "title": "intelligence artificielle"}]}
        with self.assertRaises(ValueError):
            validate_clip_candidates(raw, self.segments, 3)

    def test_rejects_overlapping_clips(self) -> None:
        raw = {
            "clips": [
                {"start_index": 0, "end_index": 1, "title": "La question importante est"},
                {"start_index": 1, "end_index": 2, "title": "Il faut regarder les usages"},
            ]
        }
        clips = validate_clip_candidates(raw, self.segments, 3)
        self.assertEqual(len(clips), 1)

    def test_paris_schedule_uses_consecutive_local_days(self) -> None:
        first = parse_publish_time("2026-10-14T17:00:00+02:00", datetime(2026, 10, 13, 10, tzinfo=timezone.utc))
        self.assertEqual(
            daily_publish_times(first, 2),
            ["2026-10-14T15:00:00Z", "2026-10-15T15:00:00Z"],
        )

    def test_schedule_keeps_five_pm_when_paris_changes_to_winter_time(self) -> None:
        first = parse_publish_time("2026-10-24T17:00:00+02:00", datetime(2026, 10, 13, 10, tzinfo=timezone.utc))
        times = daily_publish_times(first, 2)
        self.assertEqual(times, ["2026-10-24T15:00:00Z", "2026-10-25T16:00:00Z"])
        self.assertEqual(format_publish_time(times[1]), "2026-10-25 17:00 CET (Paris)")

    def test_publish_time_requires_timezone_and_future_date(self) -> None:
        with self.assertRaises(ValueError):
            parse_publish_time("2026-10-14T17:00:00", datetime(2026, 10, 13, 10, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            parse_publish_time("2026-10-12T17:00:00+02:00", datetime(2026, 10, 13, 10, tzinfo=timezone.utc))

    def test_default_publish_time_is_tomorrow_at_five_in_paris(self) -> None:
        now = datetime(2026, 10, 13, 12, tzinfo=timezone.utc)
        self.assertEqual(next_publish_time(now).isoformat(), "2026-10-14T17:00:00+02:00")

    def test_subtitles_are_relative_to_clip_start(self) -> None:
        result = make_srt(self.segments, 8, 32)
        self.assertIn("00:00:00,000 --> 00:00:11,500", result)
        self.assertIn("La question importante est qui contrôle les données.", " ".join(result.split()))


if __name__ == "__main__":
    unittest.main()
