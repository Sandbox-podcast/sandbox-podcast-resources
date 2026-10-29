from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import unittest
import wave

from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling_browser import prepare, record_attempt, complete_request, mark_unknown


def wav_file(path, seconds=.3):
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x00\x00" * round(48000 * seconds))
    return path


def browser_script():
    return {"story_id": "browser-story", "budget": {"limit": 0, "currency": "EUR", "browser_credit_limit": 100},
            "speakers": {"narrator": {"name": "Non prononcé", "voice": {"provider": "elevenlabs_browser", "name": "Voix choisie dans ElevenLabs",
                "authorization": "Voix autorisée du compte connecté."}}},
            "scenes": [{"scene_id": "opening", "utterances": [
                {"utterance_id": "a", "speaker_id": "narrator", "text": "La grille est ouverte.", "delivery": {"emotion": "curieux"}},
                {"utterance_id": "b", "speaker_id": "narrator", "text": "La barque revient.", "delivery": {}}],
                "sound": {"music": {"provider": "elevenlabs_browser", "prompt": "Nappe instrumentale discrète, piano lent.", "purpose": "Attente calme.", "duration_seconds": 5}}}]}


class BrowserHandoffTests(unittest.TestCase):
    def test_speaker_voice_is_stable_across_completed_utterances(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            script = browser_script()
            script["scenes"][0]["sound"] = {}
            rows = prepare(store, script, root / "requests")["requests"]
            self.assertTrue(all(r["spec"]["speaker_id"] == "narrator" for r in rows))
            audio = wav_file(root / "download.wav")
            for row in rows:
                record_attempt(store, row["request_id"], 100, 20, "Estimation de recette.")
            complete_request(store, rows[0]["request_id"], audio,
                             {"voice_name": "Voix A", "voice_id": "voice-a", "evidence": "Voix A sélectionnée dans la session de recette."})
            with self.assertRaisesRegex(ValueError, "speaker_voice_mismatch"):
                complete_request(store, rows[1]["request_id"], audio,
                                 {"voice_name": "Voix B", "voice_id": "voice-b", "evidence": "Autre sélection."})
            with self.assertRaisesRegex(ValueError, "speaker_voice_mismatch"):
                complete_request(store, rows[1]["request_id"], audio,
                                 {"voice_name": "Voix A", "voice_id": "different-id", "evidence": "Même nom mais identifiant différent."})
            self.assertEqual(store.get("storytelling_browser_request", rows[1]["request_id"])["status"], "submitted")
            result = complete_request(store, rows[1]["request_id"], audio,
                                      {"voice_name": "Voix A", "voice_id": "voice-a", "evidence": "Sélection identique vérifiée dans la recette."})
            self.assertEqual(result["status"], "completed")
            self.assertEqual(store.get("storytelling_browser_voice", "browser-story:narrator")["voice_id"], "voice-a")

    def test_explicit_configured_voice_cannot_be_replaced_on_first_result(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            script = browser_script()
            script["speakers"]["narrator"]["voice"]["name"] = "Voix demandée"
            row = prepare(store, script, root / "requests")["requests"][0]
            record_attempt(store, row["request_id"], 100, 20, "Estimation de recette.")
            with self.assertRaisesRegex(ValueError, "configured_voice_mismatch"):
                complete_request(store, row["request_id"], wav_file(root / "audio.wav"),
                                 {"voice_name": "Autre voix", "evidence": "Une autre voix a été sélectionnée."})
            self.assertEqual(store.get("storytelling_browser_request", row["request_id"])["status"], "submitted")
            self.assertIsNone(store.get("storytelling_browser_voice", "browser-story:narrator"))

    def test_speech_result_requires_observed_voice_name(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            row = prepare(store, browser_script(), root / "requests")["requests"][0]
            record_attempt(store, row["request_id"], 100, 20, "Estimation de recette.")
            audio = wav_file(root / "audio.wav")
            for provenance in ({"evidence": "Nom de voix absent."}, {"voice_name": "Voix choisie dans ElevenLabs", "evidence": "Sélection non précisée."}):
                with self.subTest(provenance=provenance), self.assertRaisesRegex(ValueError, "voice_name_required"):
                    complete_request(store, row["request_id"], audio, provenance)

    def test_partial_completion_resolves_only_after_all_resources_exist(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            source = wav_file(root / "download.wav")
            script = browser_script()
            first = prepare(store, script, root / "requests")
            self.assertFalse(first["ready"])
            self.assertEqual(len(first["requests"]), 3)
            speech = [r for r in first["requests"] if r["kind"] == "speech"]
            self.assertEqual(speech[0]["spec"]["text"], "La grille est ouverte.")
            self.assertNotIn("Non prononcé", speech[0]["spec"]["text"])
            self.assertNotIn("curieux", speech[0]["spec"]["text"])
            for row in first["requests"]:
                record_attempt(store, row["request_id"], 100, 20, "Estimation visible dans ElevenLabs avant soumission.")
                complete_request(store, row["request_id"], source, {"provider": "ElevenLabs", "surface": "web", "voice_name": "Voix de recette", "evidence": "Téléchargement du résultat depuis le compte connecté."})
            ready = prepare(store, script, root / "requests")
            self.assertTrue(ready["ready"])
            self.assertEqual(ready["script"]["speakers"]["narrator"]["voice"]["provider"], "recordings")
            self.assertEqual(set(ready["script"]["speakers"]["narrator"]["voice"]["recordings"]), {"a", "b"})
            self.assertEqual(ready["script"]["scenes"][0]["sound"]["music"]["provider"], "recordings")
            self.assertEqual(script["speakers"]["narrator"]["voice"]["provider"], "elevenlabs_browser")

    def test_changed_line_reuses_independent_browser_requests(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            script = browser_script()
            first = prepare(store, script, Path(directory) / "requests")
            script["scenes"][0]["utterances"][0]["text"] = "La grille se referme."
            second = prepare(store, script, Path(directory) / "requests")
            a = {r["anchor"]: r["request_id"] for r in first["requests"]}
            b = {r["anchor"]: r["request_id"] for r in second["requests"]}
            self.assertNotEqual(a["a-part0"], b["a-part0"])
            self.assertEqual(a["b-part0"], b["b-part0"])
            self.assertEqual(a["opening:0"], b["opening:0"])

    def test_long_speech_is_split_then_captioned_at_measured_boundaries(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            script = browser_script()
            script["budget"]["browser_credit_limit"] = 10000
            script["scenes"][0]["sound"] = {}
            script["scenes"][0]["utterances"] = script["scenes"][0]["utterances"][:1]
            script["scenes"][0]["utterances"][0]["text"] = "Une phrase qui donne une information précise. " * 20
            first = prepare(store, script, root / "requests")
            self.assertGreater(len(first["requests"]), 1)
            for row in first["requests"]:
                self.assertLessEqual(len(row["spec"]["text"]), 250)
                record_attempt(store, row["request_id"], 10000, 250, "Estimation de crédits observée.")
                complete_request(store, row["request_id"], wav_file(root / "chunk.wav", seconds=.4), {"voice_name": "Voix de recette", "evidence": "Téléchargement du segment observé."})
            ready = prepare(store, script, root / "requests")
            ref = ready["script"]["speakers"]["narrator"]["voice"]["recordings"]["a"]
            self.assertEqual(len(ref["caption_segments"]), len(first["requests"]))
            for index, segment in enumerate(ref["caption_segments"]):
                self.assertAlmostEqual(segment["start_seconds"], index * .4, places=4)
                self.assertAlmostEqual(segment["end_seconds"], (index + 1) * .4, places=4)

    def test_unknown_submission_cannot_be_replayed_and_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            rows = prepare(store, browser_script(), Path(directory) / "requests")["requests"]
            key = rows[0]["request_id"]
            record_attempt(store, key, 100, 80, "Coût estimé observé.")
            mark_unknown(store, key, "La session s'est interrompue après le clic Générer.")
            with self.assertRaisesRegex(ValueError, "reconcile_required"):
                record_attempt(store, key, 100, 80, "Relance interdite.")
            with self.assertRaisesRegex(ValueError, "credit_limit_exceeded"):
                record_attempt(store, rows[1]["request_id"], 100, 21, "Autre opération.")
            script = browser_script()
            script["scenes"][0]["utterances"][0]["text"] = "Modification après résultat inconnu."
            changed = prepare(store, script, Path(directory) / "requests")["requests"][0]
            with self.assertRaisesRegex(ValueError, "reconcile_required"):
                record_attempt(store, changed["request_id"], 100, 10, "Une correction ne peut masquer la tentative incertaine.")

    def test_absent_authorization_cannot_be_replaced_by_attempt_argument(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            script = browser_script()
            del script["budget"]["browser_credit_limit"]
            key = prepare(store, script, Path(directory) / "requests")["requests"][0]["request_id"]
            with self.assertRaisesRegex(ValueError, "credit_limit_required"):
                record_attempt(store, key, 1000, 10, "Plafond absent du cadrage.")

    def test_concurrent_attempts_share_a_credit_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            with Store(state) as store:
                rows = prepare(store, browser_script(), Path(directory) / "requests")["requests"][:2]
            barrier = threading.Barrier(2)
            def submit(row):
                with Store(state) as store:
                    barrier.wait()
                    try:
                        record_attempt(store, row["request_id"], 100, 60, "Estimation observée.")
                        return True
                    except ValueError:
                        return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(sorted(pool.map(submit, rows)), [False, True])

    def test_result_tampering_is_not_silently_regenerated(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            script = browser_script()
            del script["scenes"][0]["sound"]["music"]
            script["scenes"][0]["utterances"] = script["scenes"][0]["utterances"][:1]
            row = prepare(store, script, root / "requests")["requests"][0]
            record_attempt(store, row["request_id"], 100, 20, "Estimation observée.")
            completed = complete_request(store, row["request_id"], wav_file(root / "download.wav"), {"voice_name": "Voix de recette", "evidence": "Téléchargement observé."}, actual_credits=18)
            Path(completed["result"]["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "result_changed"):
                prepare(store, script, root / "requests")

    def test_cookie_or_secret_provenance_fields_are_refused(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            key = prepare(store, browser_script(), root / "requests")["requests"][0]["request_id"]
            record_attempt(store, key, 100, 10, "Soumission observée.")
            with self.assertRaisesRegex(ValueError, "provenance_fields_invalid"):
                complete_request(store, key, wav_file(root / "audio.wav"), {"evidence": "Visible", "cookie": "secret"})


if __name__ == "__main__":
    unittest.main()
