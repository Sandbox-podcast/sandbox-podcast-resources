"""Portable browser assets and caches survive loss of original files."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_storytelling_browser import browser_script, wav_file
from youtube_growth.factory.backups import backup, restore
from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling_audio import produce_audio
from youtube_growth.factory.storytelling_browser import prepare, record_attempt, complete_request


class PortableBrowserRecipe(unittest.TestCase):
    def test_browser_results_and_voice_cache_survive_without_originals(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            script = browser_script()
            script["scenes"][0]["sound"] = {}
            download = wav_file(root / "download.wav")
            browser_dir = state / "storytelling/browser-project/browser"
            audio_dir = state / "storytelling/browser-project/audio"
            with Store(state) as store:
                pending = prepare(store, script, browser_dir)
                for row in pending["requests"]:
                    record_attempt(store, row["request_id"], 100, 10,
                                   "Fixture technique sans génération réelle.")
                    complete_request(store, row["request_id"], download,
                                     {"provider": "ElevenLabs", "surface": "synthetic_test",
                                      "voice_name": "Voix de recette",
                                      "evidence": "PCM synthétique pour contrôler la restauration."},
                                     actual_credits=0)
                ready = prepare(store, script, browser_dir)
                original_audio = produce_audio(store, {}, ready["script"], audio_dir, synthetic=True)
                original_hashes = [u["sha256"] for s in original_audio["scenes"] for u in s["utterances"]]
                store.put("storytelling_project", script["story_id"],
                          {"story_id": script["story_id"], "artifacts": ready["artifacts"] + original_audio["artifacts"],
                           "browser_requests": ready["requests"], "audio": original_audio})
                snapshot = root / "snapshot.sqlite3"
                receipt = backup(store, snapshot, include_media=True)
                self.assertGreater(len(receipt["files"]), 0)

            self.assertTrue(state.resolve().is_relative_to(root.resolve()))
            state.rename(root / "unavailable-original")
            download.unlink()
            target = root / "restored"
            self.assertEqual(restore(snapshot, target)["status"], "restored_paused")
            with Store(target) as store:
                rows = store.records("storytelling_browser_request")
                self.assertEqual(len(rows), 2)
                for row in rows:
                    self.assertEqual(row["status"], "completed")
                    for field in ("request_file", "result"):
                        self.assertTrue(Path(row[field]["path"]).is_relative_to(target))
                ready = prepare(store, script, target / "storytelling/browser-project/browser")
                self.assertTrue(ready["ready"])
                mtimes = {p: p.stat().st_mtime_ns for p in (target / "storytelling-cache/audio").glob("*/speech.wav")}
                self.assertTrue(mtimes)
                with patch("youtube_growth.factory.storytelling_audio._system", side_effect=AssertionError("Unexpected synthesis")), \
                     patch("youtube_growth.factory.storytelling_audio.ElevenLabsClient", side_effect=AssertionError("Unexpected provider access")):
                    reused = produce_audio(store, {}, ready["script"], target / "storytelling/browser-project/audio", synthetic=True)
                self.assertEqual(original_hashes, [u["sha256"] for s in reused["scenes"] for u in s["utterances"]])
                self.assertTrue(all(p.stat().st_mtime_ns == mtime for p, mtime in mtimes.items()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
