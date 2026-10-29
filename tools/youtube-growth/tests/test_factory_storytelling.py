import tempfile
import unittest
from pathlib import Path

from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling import frame


class StorytellingFrameTests(unittest.TestCase):
    def test_questions_defaults_and_revisions(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            first = frame(store, {"topic": "Un sujet"})
            self.assertEqual([q["field"] for q in first["questions"]], ["mode", "autonomy", "budget"])
            self.assertEqual(first["brief"]["duration_minutes"], 20)
            second = frame(store, {"story_id": first["story_id"], "topic": "Un sujet", "mode": "fiction",
                                   "autonomy": "autonomous", "budget": {"limit": 0, "currency": "EUR"}})
            self.assertEqual(second["status"], "framed")
            self.assertEqual(second["production_status"], "ready")
            self.assertEqual(len(store.records("storytelling_revision")), 2)
            self.assertEqual(store.get("storytelling", first["story_id"])["revision"], second["revision"])

    def test_invalid_budget_never_persisted(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            for limit in (-1, float("nan"), True):
                with self.assertRaises(ValueError):
                    frame(store, {"topic": "Sujet", "budget": {"limit": limit, "currency": "EUR"}})
            self.assertEqual(store.records("storytelling"), [])


if __name__ == "__main__":
    unittest.main()
