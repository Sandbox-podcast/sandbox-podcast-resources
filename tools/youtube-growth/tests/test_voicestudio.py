from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.parse import parse_qs
import wave

from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling_audio import produce_audio
from youtube_growth.factory.storytelling_contracts import validate_script
from youtube_growth.factory.voicestudio import (VoiceStudio, VoiceStudioError, discover, interpretation_plan, live_voice,
                                                request_fields, sample, selection)

LOU = {"id": "f92d4b17", "name": "Lou", "kind": "clone", "language": "French", "ref_audio_path": "f92d4b17.wav",
       "ref_text": "Texte de référence personnel.", "audio_url": "/profiles/f92d4b17/audio?v=1", "is_locked": 0,
       "locked_audio_path": "", "seed": None, "instruct": "", "is_demo": 0, "consent_basis": "own_voice",
       "consent_attested_at": "2026-10-30T21:41:07Z"}
ENGINES = [{"id": "voxcpm2", "available": True, "supports_cloning": True, "supports_voice_design": True, "supports_emotion": False, "instruct_vocabulary": "freeform"},
           {"id": "omnivoice", "available": True, "supports_cloning": True, "supports_voice_design": True, "supports_emotion": False, "instruct_vocabulary": "tags"},
           {"id": "kittentts", "available": True, "supports_cloning": False, "supports_voice_design": False, "instruct_vocabulary": "freeform", "preset_voices": ["a"]},
           {"id": "indextts2", "available": False, "supports_cloning": True, "supports_emotion": True}]
PRESETS = [{"id": p, "label": p.title(), "description": "DSP"} for p in ("broadcast", "cinematic", "podcast", "raw", "warm", "bright")]


def wav_bytes(seconds=.4):
    target = io.BytesIO()
    with wave.open(target, "wb") as stream:
        stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x10\x00" * round(48000 * seconds))
    return target.getvalue()


class FakeVoiceStudio:
    """Loopback stand-in for the documented 0.5.7 routes; it never synthesizes speech."""
    def __init__(self, version="0.5.7"):
        self.version, self.profiles, self.calls = version, [dict(LOU)], []
        fake = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def reply(self, value, code=200, content_type="application/json"):
                body = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def do_GET(self):
                routes = {"/health": {"status": "ok", "version": fake.version, "device": "cpu"}, "/profiles": fake.profiles,
                          "/engines/tts": {"active": "voxcpm2", "backends": ENGINES}, "/engines/effects/presets": {"presets": PRESETS}}
                self.reply(routes[self.path]) if self.path in routes else self.reply({"detail": "Not Found"}, 404)
            def do_POST(self):
                fields = {k: v[0] for k, v in parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")).items()}
                fake.calls.append(fields)
                if fields.get("engine") == "kittentts":
                    return self.reply({"detail": "KittenTTS can't use reference audio"}, 422)
                self.reply(wav_bytes(), content_type="audio/wav")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class VoiceStudioTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeVoiceStudio()
        self.client = VoiceStudio(self.fake.url)

    def tearDown(self):
        self.fake.close()

    def test_discovery_lists_current_profiles_without_personal_reference(self):
        found = discover(self.client)
        self.assertEqual([p["name"] for p in found["profiles"]], ["Lou"])
        self.assertEqual(found["profiles"][0]["consent"], "own_voice_attested")
        self.assertEqual(found["profiles"][0]["usable_engines"], ["voxcpm2", "omnivoice"])
        self.assertNotIn("Texte de référence", json.dumps(found, ensure_ascii=False))
        self.assertNotIn("indextts2", [e["id"] for e in found["engines"]])
        # A profile recorded later by another member appears without code change.
        self.fake.profiles.append({**LOU, "id": "a1b2c3d4", "name": "Nico", "consent_basis": "", "consent_attested_at": None})
        later = discover(self.client)
        self.assertEqual([(p["name"], p["consent"]) for p in later["profiles"]], [("Lou", "own_voice_attested"), ("Nico", "not_recorded")])
        with self.assertRaisesRegex(VoiceStudioError, "authorization_required"):
            selection(later, "a1b2c3d4")
        self.assertIn("accord de Nico", selection(later, "a1b2c3d4", authorization="Voix utilisée avec l'accord de Nico.")["voice"]["authorization"])
        # A designed voice needs an engine that reads a description, not a reference clip.
        self.fake.profiles.append({**LOU, "id": "d1d1d1d1", "name": "Voix conçue", "kind": "design", "ref_audio_path": "", "instruct": "female, 30s"})
        designed = next(p for p in discover(self.client)["profiles"] if p["profile_id"] == "d1d1d1d1")
        self.assertEqual(designed["usable_engines"], ["voxcpm2", "omnivoice"])

    def test_a_newer_voice_studio_invalidates_the_pinned_voice(self):
        voice = selection(discover(self.client), "f92d4b17")["voice"]
        self.fake.version = "0.6.0"
        with self.assertRaisesRegex(VoiceStudioError, "version_changed_select_again"):
            live_voice(self.client, voice)
        found = discover(self.client)
        self.assertEqual(found["verification"], "controls_unverified_for_this_version")
        again = selection(found, "f92d4b17")["voice"]
        self.assertEqual((again["voicestudio_version"], set(again["settings"])), ("0.6.0", {"effect_preset", "pause_between_sentences_seconds"}))
        self.assertEqual(live_voice(self.client, again)["version"], "0.6.0")

    def test_plan_applies_only_controls_that_the_engine_uses(self):
        found = discover(self.client)
        voxcpm = selection(found, "f92d4b17", video_type="commentary", register="dynamic")
        self.assertNotIn("speed", voxcpm["voice"]["settings"])
        self.assertEqual(voxcpm["plan"]["engine_controls"]["not_applied"][0]["control"], "speed")
        self.assertEqual(voxcpm["plan"]["engine_controls"]["optional_trials"][0]["control"], "instruct")
        omni = selection(found, "f92d4b17", engine="omnivoice", video_type="commentary", register="dynamic")
        self.assertEqual(omni["voice"]["settings"]["speed"], 1.08)
        with self.assertRaisesRegex(VoiceStudioError, "speed_not_applied"):
            selection(found, "f92d4b17", settings={"speed": 1.1})
        with self.assertRaisesRegex(VoiceStudioError, "instruct_not_supported"):
            selection(found, "f92d4b17", engine="omnivoice", settings={"instruct": "calm"})
        with self.assertRaisesRegex(VoiceStudioError, "not_usable"):
            selection(found, "f92d4b17", engine="kittentts")
        plan = interpretation_plan("documentary", "voxcpm2", "9.9.9", presets=PRESETS)
        self.assertEqual(set(plan["settings"]), {"effect_preset", "pause_between_sentences_seconds"})
        self.assertIn("traitement", plan["processing"]["note"].lower())

    def test_live_check_and_request_keep_the_pinned_voice(self):
        voice = selection(discover(self.client), "f92d4b17")["voice"]
        self.assertEqual(live_voice(self.client, voice)["profile_name"], "Lou")
        fields = request_fields(voice, "Bonjour.")
        self.assertEqual({k: fields[k] for k in ("profile_id", "engine", "language", "seed", "num_step")},
                         {"profile_id": "f92d4b17", "engine": "voxcpm2", "language": "French", "seed": "42", "num_step": "16"})
        self.assertNotIn("speed", fields)
        self.assertNotIn("pause_between_sentences_seconds", fields)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "essai.wav"
            self.assertEqual(sample(self.client, voice, "Bonjour.", output)["listening"], "pending")
            with self.assertRaisesRegex(VoiceStudioError, "sample_exists"):
                sample(self.client, voice, "Bonjour.", output)
        self.fake.profiles[0]["audio_url"] = "/profiles/f92d4b17/audio?v=2"
        with self.assertRaisesRegex(VoiceStudioError, "profile_changed"):
            live_voice(self.client, voice)
        self.fake.profiles.clear()
        with self.assertRaisesRegex(VoiceStudioError, "profile_missing"):
            live_voice(self.client, voice)
        with self.assertRaises(VoiceStudioError) as caught:
            VoiceStudio("http://192.0.2.1:3900")
        self.assertEqual(str(caught.exception), "voicestudio_loopback_url_required")

    def test_unavailable_service_is_reported(self):
        self.fake.close()
        found = discover(self.client)
        self.assertEqual((found["status"], found["error"]), ("unavailable", "voicestudio_unavailable"))
        self.fake = FakeVoiceStudio()

    def test_script_contract_accepts_a_pinned_voicestudio_voice(self):
        voice = selection(discover(self.client), "f92d4b17")["voice"]
        script = _script(voice)
        self.assertEqual(validate_script(script, [])["speakers"]["narrator"]["voice"]["provider"], "voicestudio")
        broken = _script({k: v for k, v in voice.items() if k != "profile_revision"})
        with self.assertRaisesRegex(ValueError, "voice_incomplete"):
            validate_script(broken, [])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg requis")
    def test_production_generates_one_measured_take_per_sentence_and_reuses_it(self):
        voice = selection(discover(self.client), "f92d4b17")["voice"]
        config = {"voicestudio": {"base_url": self.fake.url, "timeout_seconds": 30}}
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            script = _script(voice)
            audio = produce_audio(store, config, script, Path(directory) / "audio")
            line = audio["scenes"][0]["utterances"][0]
            self.assertEqual(len(self.fake.calls), 2)
            self.assertEqual([c["text"] for c in self.fake.calls], ["Premier temps du récit.", "Second temps."])
            self.assertEqual(line["provider_metadata"]["profile_id"], "f92d4b17")
            self.assertEqual(line["alignment_kind"], "measured_caption_chunks")
            first, second = line["caption_segments"]
            self.assertAlmostEqual(second["start_seconds"] - first["end_seconds"], .3, places=2)
            produce_audio(store, config, script, Path(directory) / "audio-again")
            self.assertEqual(len(self.fake.calls), 2)
            script["scenes"][0]["utterances"][0]["delivery"] = {"speed": 1.1}
            with self.assertRaisesRegex(ValueError, "speed_not_applied"):
                produce_audio(store, config, script, Path(directory) / "audio-speed")


def _script(voice):
    return {"version": 1, "story_id": "story", "title": "Titre", "mode": "fiction", "budget": {"limit": 0, "currency": "EUR"},
            "narrative": {"structure": "idea", "question": "Question ?", "interest": "Intérêt.", "vehicle": "Support.",
                          "initial": "Avant.", "answer": "Réponse."},
            "continuity": {"characters": [], "locations": [], "chronology": [], "motifs": [], "visual_style": "Sobre."},
            "speakers": {"narrator": {"name": "Lou", "voice": voice}}, "facts": [],
            "scenes": [{"scene_id": "s1", "version": 1, "function": "Ouvrir.", "knowledge_before": "Rien.", "knowledge_after": "Le cadre.",
                        "factual_status": "fiction", "fact_ids": [],
                        "utterances": [{"utterance_id": "u1", "speaker_id": "narrator", "text": "Premier temps du récit. Second temps.", "delivery": {}}],
                        "shots": [{"shot_id": "p1", "utterance_ids": ["u1"], "description": "Schéma.", "purpose": "explanation",
                                   "type": "diagram", "labels": ["Cadre"]}], "sound": {}}]}


if __name__ == "__main__":
    unittest.main()
