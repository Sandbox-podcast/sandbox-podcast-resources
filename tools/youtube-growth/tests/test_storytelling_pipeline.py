"""Business flow tests and an opt-in real Windows speech/render recipe."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave

from youtube_growth.factory.contracts import instant, iso, load_config
from youtube_growth.factory import storytelling
from youtube_growth.factory.storytelling_render import artifact, build_timeline, render
from youtube_growth.factory.storytelling_audio import produce_audio
from youtube_growth.factory.store import Store


def brief_fixture(autonomy="autonomous"):
    return {"story_id": "pipeline-fixture", "topic": "Fiction de recette : le quai", "notes": "Scénario fictif, sans faits ni personnes réels.",
            "mode": "fiction", "autonomy": autonomy, "budget": {"limit": 0, "currency": "EUR"}, "duration_minutes": .25}


def script_fixture():
    return {"version": 1, "story_id": "pipeline-fixture", "title": "La grille du quai", "mode": "fiction",
        "budget": {"limit": 0, "currency": "EUR"},
        "narrative": {"question": "La grille restera-t-elle ouverte ?", "interest": "Une personne revient de l'île.", "vehicle": "La gardienne du quai",
            "initial": "La journée semble terminée.", "answer": "La gardienne attend le dernier retour.", "structure": "human"},
        "speakers": {"n": {"name": "Narratrice", "voice": {"provider": "system", "name": "Microsoft Hortense Desktop", "authorization": "Voix standard Windows de recette, sans clonage."}}},
        "continuity": {"characters": ["La gardienne"], "locations": ["Le quai"], "chronology": ["Le soir"], "visual_style": "Schéma bleu et cyan.", "motifs": ["La grille"]},
        "facts": [], "scenes": [
            {"scene_id": "opening", "version": 1, "function": "Le quai vide", "knowledge_before": "La gardienne ferme.", "knowledge_after": "Une barque revient.", "factual_status": "fiction", "fact_ids": [],
             "utterances": [{"utterance_id": "a", "speaker_id": "n", "text": "La gardienne aperçoit une barque.", "delivery": {}}],
             "shots": [{"shot_id": "first", "utterance_ids": ["a"], "type": "diagram", "purpose": "situation", "description": "La grille et la barque sur l'eau.", "labels": ["Le quai", "La barque"]}], "sound": {}},
            {"scene_id": "ending", "version": 1, "function": "Le dernier retour", "knowledge_before": "Le passage est fermé.", "knowledge_after": "La passagère rejoint la rive.", "factual_status": "fiction", "fact_ids": [],
             "utterances": [{"utterance_id": "b", "speaker_id": "n", "text": "Elle rouvre la grille du quai.", "delivery": {}}],
             "shots": [{"shot_id": "last", "utterance_ids": ["b"], "type": "diagram", "purpose": "situation", "description": "La grille ouverte, la passagère à terre.", "labels": ["La grille ouverte", "Le retour"]}], "sound": {}}]}


def measured_audio(script, directory, total=15.):
    """Explicit silent PCM test double; no provider validation is claimed."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cursor, rows, artifacts = 0., [], []
    count = sum(len(s["utterances"]) for s in script["scenes"])
    duration = total / count
    for scene in script["scenes"]:
        start = cursor
        utterances = []
        path = directory / (scene["scene_id"] + ".wav")
        with wave.open(str(path), "wb") as stream:
            stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            stream.writeframes(b"\x00\x00" * round(48000 * duration * len(scene["utterances"])))
        for u in scene["utterances"]:
            utterances.append({**u, "start_seconds": cursor, "end_seconds": cursor + duration,
                               "path": str(path), "sha256": artifact(path)["sha256"], "alignment": "synthetic_test_boundary"})
            cursor += duration
        rows.append({"scene_id": scene["scene_id"], "start_seconds": start, "duration_seconds": cursor - start,
                     "path": str(path), "sha256": artifact(path)["sha256"], "utterances": utterances})
        artifacts.append(artifact(path))
    return {"scenes": rows, "duration_seconds": cursor, "artifacts": artifacts, "provider_validation": "synthetic_test_double", "sound_tracks": []}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state")
        self.addCleanup(self.store.close)
        self.config = load_config()

    def prepare(self, autonomy="autonomous", extra=None):
        brief = {**brief_fixture(autonomy), **(extra or {})}
        storytelling.frame(self.store, brief)
        return storytelling.import_script(self.store, brief["story_id"], script_fixture())

    def fake_audio(self, store, config, script, directory, **kwargs):
        return measured_audio(script, directory)

    def fake_render(self, script, timeline, audio, directory, **kwargs):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "test-double.mp4"
        path.write_bytes(b"synthetic-render-test-double")
        return {**artifact(path), "duration_seconds": timeline["duration_seconds"], "artifacts": [artifact(path)], "synthetic": True}

    def test_approval_stops_before_audio_and_script_edit_invalidates_it(self):
        self.prepare("editorial_review")
        with patch("youtube_growth.factory.storytelling_audio.produce_audio", side_effect=self.fake_audio) as audio, patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            first = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
            self.assertEqual(first["status"], "awaiting_approval")
            audio.assert_not_called()
            storytelling.control(self.store, "pipeline-fixture", "approve")
            completed = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
            self.assertEqual(completed["status"], "completed")
            changed = script_fixture()
            changed["scenes"][1]["utterances"][0]["text"] = "La grille reste ouverte pour le retour."
            changed["scenes"][1]["version"] += 1
            project = storytelling.import_script(self.store, "pipeline-fixture", changed)
            self.assertNotIn("approval", project)
            audio.reset_mock()
            self.assertEqual(storytelling.run(self.store, self.config, "pipeline-fixture")["status"], "awaiting_approval")
            audio.assert_not_called()

    def test_pause_blocks_work_and_resume_uses_same_project(self):
        self.prepare()
        storytelling.control(self.store, "pipeline-fixture", "pause")
        with patch("youtube_growth.factory.storytelling_audio.produce_audio", side_effect=self.fake_audio) as audio, patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            with self.assertRaisesRegex(ValueError, "storytelling_paused"):
                storytelling.run(self.store, self.config, "pipeline-fixture")
            audio.assert_not_called()
            self.assertEqual(self.store.get("storytelling_project", "pipeline-fixture")["status"], "paused")
            storytelling.control(self.store, "pipeline-fixture", "resume")
            self.assertEqual(storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)["status"], "completed")

    def test_frozen_source_survives_original_disappearance(self):
        source = self.root / "notes.txt"
        source.write_text("Document de recette fictif.", encoding="utf-8")
        project = self.prepare(extra={"documents": [str(source)]})
        paths = [a["path"] for a in project["sources"]["artifacts"]]
        source.unlink()
        with patch("youtube_growth.factory.storytelling_audio.produce_audio", side_effect=self.fake_audio), patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            result = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(all(Path(path).is_file() for path in paths))

    def test_lock_allows_unrelated_scene_edit_but_refuses_locked_change(self):
        self.prepare()
        storytelling.control(self.store, "pipeline-fixture", "lock", scene_id="opening")
        changed = script_fixture()
        changed["scenes"][1]["utterances"][0]["text"] = "La gardienne garde la grille ouverte."
        storytelling.import_script(self.store, "pipeline-fixture", changed)
        changed["scenes"][0]["utterances"][0]["text"] = "La barque est déjà au quai."
        with self.assertRaisesRegex(ValueError, "storytelling_scene_locked"):
            storytelling.import_script(self.store, "pipeline-fixture", changed)

    def test_locked_scene_also_locks_its_global_voice_parameters(self):
        self.prepare()
        storytelling.control(self.store, "pipeline-fixture", "lock", scene_id="opening")
        changed = script_fixture()
        changed["speakers"]["n"]["voice"]["rate"] = 2
        with self.assertRaisesRegex(ValueError, "storytelling_scene_dependency_locked"):
            storytelling.import_script(self.store, "pipeline-fixture", changed)
        unchanged = self.store.get("storytelling_project", "pipeline-fixture")
        saved = json.loads(Path(unchanged["script"]["path"]).read_text(encoding="utf-8"))
        self.assertNotIn("rate", saved["speakers"]["n"]["voice"])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for imported browser audio")
    def test_browser_pending_then_completed_files_continue_without_provider_api(self):
        from youtube_growth.factory.storytelling_browser import record_attempt, complete_request
        brief = {**brief_fixture(), "audio_workflow": "elevenlabs_browser",
                 "budget": {"limit": 0, "currency": "EUR", "browser_credit_limit": 1000}}
        storytelling.frame(self.store, brief)
        script = script_fixture()
        script["budget"] = brief["budget"]
        script["speakers"]["n"]["voice"] = {"provider": "elevenlabs_browser", "name": "Voix choisie dans ElevenLabs",
                                                  "authorization": "Voix du compte connecté via navigateur."}
        storytelling.import_script(self.store, "pipeline-fixture", script)
        with patch("youtube_growth.factory.storytelling_audio.ElevenLabsClient", side_effect=AssertionError("Aucun client API ne doit être créé")), patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            waiting = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
            self.assertEqual(waiting["status"], "awaiting_browser_audio")
            self.assertTrue(waiting["browser_requests"])
            for index, row in enumerate(waiting["browser_requests"]):
                download = self.root / ("download-" + str(index) + ".wav")
                with wave.open(str(download), "wb") as output:
                    output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                    output.writeframes(b"\x00\x00" * (48000 * (index + 1)))
                record_attempt(self.store, row["request_id"], 1000, 100, "Crédits de recette simulés, aucun appel fournisseur.")
                complete_request(self.store, row["request_id"], download,
                                 {"provider": "ElevenLabs", "surface": "test_double", "voice_name": "Voix de recette", "evidence": "Fichier PCM synthétique de test, aucune génération réelle."})
            completed = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
            self.assertEqual(completed["status"], "completed")
            self.assertAlmostEqual(completed["audio"]["duration_seconds"], 3., places=3)
            timeline = json.loads(Path(completed["timeline"]["path"]).read_text(encoding="utf-8"))
            self.assertEqual(timeline["clock"], "measured_audio")
            self.assertTrue(all(c["alignment"] == "measured_audio_chunks" for c in timeline["captions"]))

    def imported_music_project(self, rights="owned", extra=None, cue=None):
        music = self.root / "synthetic-music.wav"
        with wave.open(str(music), "wb") as output:
            output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            output.writeframes(b"\x00\x00" * 24000)
        brief = {**brief_fixture(), "media": [str(music)], **(extra or {})}
        if rights:
            brief["media_rights"] = {str(music): rights}
        storytelling.frame(self.store, brief)
        source = next(s for s in storytelling._sources(self.store, storytelling._record(self.store, "pipeline-fixture"))["sources"] if s["media_type"] == "audio")
        script = script_fixture()
        script["budget"] = brief["budget"]
        script["scenes"][0]["sound"] = {"music": {"provider": "recordings", "source_id": source["source_id"],
                                                  "purpose": "Installer l'attente sur le quai.", "level_db": -18, **(cue or {})}}
        return script

    def test_imported_music_needs_rights_and_a_coherent_level(self):
        script = self.imported_music_project(rights=None)
        with self.assertRaisesRegex(ValueError, "Source sonore autorisée absente"):
            storytelling.import_script(self.store, "pipeline-fixture", script)
        script = self.imported_music_project(cue={"gain_db": -25})
        with self.assertRaisesRegex(ValueError, "Niveau sonore invalide"):
            storytelling.import_script(self.store, "pipeline-fixture", script)
        script = self.imported_music_project(cue={"gain_db": -18})
        storytelling.import_script(self.store, "pipeline-fixture", script)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for imported music")
    def test_imported_music_from_source_id_reaches_the_timeline_at_its_level(self):
        def system(text, voice, path):
            target = path / "system.wav"
            with wave.open(str(target), "wb") as output:
                output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                output.writeframes(b"\x00\x00" * 48000)
            return target
        storytelling.import_script(self.store, "pipeline-fixture", self.imported_music_project())
        with patch("youtube_growth.factory.storytelling_audio._system", side_effect=system), \
                patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            result = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
        self.assertEqual(result["status"], "completed")
        timeline = json.loads(Path(result["timeline"]["path"]).read_text(encoding="utf-8"))
        self.assertEqual([(t["kind"], t["provider"], t["gain_db"]) for t in timeline["sound_tracks"]], [("music", "recordings", -18)])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for imported browser audio")
    def test_browser_workflow_keeps_imported_music_resolved(self):
        from youtube_growth.factory.storytelling_browser import record_attempt, complete_request
        budget = {"limit": 0, "currency": "EUR", "browser_credit_limit": 1000}
        script = self.imported_music_project(extra={"audio_workflow": "elevenlabs_browser", "budget": budget})
        script["speakers"]["n"]["voice"] = {"provider": "elevenlabs_browser", "name": "Voix choisie dans ElevenLabs",
                                            "authorization": "Voix du compte connecté via navigateur."}
        storytelling.import_script(self.store, "pipeline-fixture", script)
        with patch("youtube_growth.factory.storytelling_render.render", side_effect=self.fake_render):
            waiting = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
            self.assertEqual(waiting["status"], "awaiting_browser_audio")
            self.assertTrue(all(row["kind"] == "speech" for row in waiting["browser_requests"]))
            for index, row in enumerate(waiting["browser_requests"]):
                download = self.root / ("download-" + str(index) + ".wav")
                with wave.open(str(download), "wb") as output:
                    output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                    output.writeframes(b"\x00\x00" * 48000)
                record_attempt(self.store, row["request_id"], 1000, 100, "Crédits de recette simulés, aucun appel fournisseur.")
                complete_request(self.store, row["request_id"], download,
                                 {"provider": "ElevenLabs", "surface": "test_double", "voice_name": "Voix de recette", "evidence": "Fichier PCM synthétique de test, aucune génération réelle."})
            completed = storytelling.run(self.store, self.config, "pipeline-fixture", synthetic=True)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual([t["gain_db"] for t in completed["audio"]["sound_tracks"]], [-18])

    def test_project_and_media_paths_cannot_traverse(self):
        brief = brief_fixture()
        brief["story_id"] = "../../escape"
        with self.assertRaises(ValueError):
            storytelling.frame(self.store, brief)
        self.prepare()
        script = script_fixture()
        script["scenes"][0]["shots"][0]["path"] = "../../private.png"
        with self.assertRaises(ValueError):
            storytelling.import_script(self.store, "pipeline-fixture", script)

    def test_worker_does_not_execute_a_job_for_a_replaced_script(self):
        self.prepare()
        now = instant("2026-10-29T12:00:00+01:00")
        job = storytelling.enqueue(self.store, "pipeline-fixture", now=now)
        changed = script_fixture()
        changed["scenes"][1]["utterances"][0]["text"] = "La grille s'ouvre pour la passagère."
        storytelling.import_script(self.store, "pipeline-fixture", changed)
        self.store.set_setting("last_collection_at", iso(now))
        self.store.set_setting("last_report_at", iso(now))
        from youtube_growth.factory.runtime import run_once
        with patch("youtube_growth.factory.runtime.watch", return_value={}), patch("youtube_growth.factory.storytelling.run") as run:
            run_once(self.store, self.config, now=now)
            run.assert_not_called()
        self.assertEqual(next(j for j in self.store.jobs() if j["id"] == job["job_id"])["status"], "completed")


class TimelineTests(unittest.TestCase):
    def test_segmented_measured_captions_follow_actual_chunk_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            script = script_fixture()
            audio = measured_audio(script, Path(directory), total=15.)
            first = audio["scenes"][0]["utterances"][0]
            first["caption_segments"] = [{"text": "La gardienne aperçoit", "start_seconds": 0., "end_seconds": 2.25},
                                         {"text": "une barque.", "start_seconds": 2.25, "end_seconds": 7.5}]
            last = audio["scenes"][1]["utterances"][0]
            last["caption_segments"] = [{"text": "Elle rouvre", "start_seconds": 0., "end_seconds": 3.},
                                        {"text": "la grille du quai.", "start_seconds": 3., "end_seconds": 7.5}]
            timeline = build_timeline(script, audio, [])
            self.assertEqual(len(timeline["captions"]), 4)
            self.assertTrue(all(c["alignment"] == "measured_audio_chunks" for c in timeline["captions"]))
            self.assertEqual(timeline["captions"][2]["start_seconds"], 7.5)
            self.assertEqual(timeline["captions"][3]["start_seconds"], 10.5)
            self.assertEqual(timeline["captions"][-1]["end_seconds"], 15.)
            self.assertEqual(" ".join(c["text"] for c in timeline["captions"]),
                             " ".join(u["text"] for s in script["scenes"] for u in s["utterances"]))

    def test_timeline_covers_every_utterance_and_holds_to_measured_end(self):
        with tempfile.TemporaryDirectory() as directory:
            script = script_fixture()
            audio = measured_audio(script, Path(directory), total=3.137)
            timeline = build_timeline(script, audio, [])
            self.assertEqual(timeline["clock"], "measured_audio")
            self.assertEqual([c["utterance_id"] for c in timeline["captions"]], ["a", "b"])
            self.assertAlmostEqual(timeline["shots"][-1]["end_seconds"], audio["duration_seconds"])
            # Quantizing shared boundaries does not accumulate a frame per shot.
            for fps in (12, 24):
                frames = sum(round(s["end_seconds"] * fps) - round(s["start_seconds"] * fps) for s in timeline["shots"])
                self.assertEqual(frames, round(audio["duration_seconds"] * fps))

    def test_missing_voice_segment_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            script = script_fixture()
            audio = measured_audio(script, Path(directory))
            audio["scenes"][0]["utterances"] = []
            with self.assertRaisesRegex(ValueError, "coverage_mismatch"):
                build_timeline(script, audio, [])

    def test_shot_cannot_claim_a_line_after_its_actual_end(self):
        with tempfile.TemporaryDirectory() as directory:
            script = script_fixture()
            scene = script["scenes"][0]
            scene["utterances"] += [{"utterance_id": "c", "speaker_id": "n", "text": "La barque avance.", "delivery": {}},
                                     {"utterance_id": "d", "speaker_id": "n", "text": "La rive apparaît.", "delivery": {}}]
            scene["shots"][0]["utterance_ids"] = ["a", "d"]
            scene["shots"].append({**scene["shots"][0], "shot_id": "crossed", "utterance_ids": ["c"]})
            audio = measured_audio(script, Path(directory))
            with self.assertRaises(ValueError):
                build_timeline(script, audio, [])


@unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1" and os.name == "nt" and shutil.which("ffmpeg"), "Recette Windows audio/vidéo explicite requise")
class RealSpeechRecipe(unittest.TestCase):
    def test_real_system_voice_and_readable_video_export(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory) / "state") as store:
            root = Path(directory)
            script = script_fixture()
            script["scenes"] = script["scenes"][:1]
            script["scenes"][0]["utterances"][0]["text"] = "La gardienne aperçoit une barque. Elle garde la grille ouverte."
            audio = produce_audio(store, load_config(), script, root / "audio")
            self.assertGreater(audio["duration_seconds"], 1)
            self.assertNotEqual(audio.get("provider_validation"), "synthetic_test_double")
            timeline = build_timeline(script, audio, [])
            result = render(script, timeline, audio, root / "preview", draft=True)
            self.assertTrue(Path(result["path"]).is_file())
            self.assertIn("La gardienne", Path(result["srt"]).read_text(encoding="utf-8"))
            self.assertAlmostEqual(result["duration_seconds"], audio["duration_seconds"], delta=.15)


if __name__ == "__main__":
    unittest.main()
