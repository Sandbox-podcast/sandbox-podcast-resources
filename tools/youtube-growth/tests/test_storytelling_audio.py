from concurrent.futures import ThreadPoolExecutor
import base64
import io
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
import wave

from youtube_growth.factory.elevenlabs import ElevenLabsClient, GenerationUnknown, ProviderError, parse_audio_response
from youtube_growth.factory.media import fingerprint
from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling_audio import _paid_audio, budget_status, produce_audio, reserve_cost, split_text, estimate_audio


def wav_bytes(seconds=.2):
    target = io.BytesIO()
    with wave.open(target, "wb") as stream:
        stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x00\x00" * round(48000 * seconds))
    return target.getvalue()


def paid_config():
    return {"storytelling": {"paid_calls_enabled": True, "elevenlabs": {"enabled": True, "currency": "EUR",
            "cost_per_character_upper_bound": .001}}}


class LedgerTests(unittest.TestCase):
    def test_concurrent_reservations_cannot_exceed_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with Store(path):
                pass
            barrier = threading.Barrier(2)
            def reserve(identity):
                with Store(path) as store:
                    barrier.wait()
                    try:
                        reserve_cost(store, "story", {"key": identity}, {"limit": 1, "currency": "EUR"}, .6)
                        return True
                    except ValueError:
                        return False
            with ThreadPoolExecutor(max_workers=2) as executor:
                self.assertEqual(sorted(executor.map(reserve, ("a", "b"))), [False, True])
            with Store(path) as store:
                self.assertAlmostEqual(budget_status(store, "story", {"limit": 1, "currency": "EUR"})["committed"], .6)

    def test_timeout_is_not_replayed_and_stays_reserved(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            story = {"story_id": "story", "budget": {"limit": 1, "currency": "EUR"}}
            calls = []
            def lost_response():
                calls.append(True)
                raise GenerationUnknown("elevenlabs_generation_unknown")
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, "reconcile_required"):
                    _paid_audio(store, paid_config(), story, {"kind": "tts"}, root, .5, lost_response)
            self.assertEqual(len(calls), 1)
            status = budget_status(store, "story", story["budget"])
            self.assertEqual(status["committed"], .5)
            self.assertEqual(len(status["unknown_calls"]), 1)
            # Shared cache identity must keep blocking if another project tries it.
            with self.assertRaisesRegex(ValueError, "reconcile_required"):
                _paid_audio(store, paid_config(), {**story, "story_id": "another-story"}, {"kind": "tts"}, root, .5, lost_response)
            self.assertEqual(len(calls), 1)

    def test_saved_response_recovers_without_new_generation(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            story = {"story_id": "story", "budget": {"limit": 1, "currency": "EUR"}}
            callback = lambda: (b"received", {"content-type": "audio/mpeg", "xi-api-key": "do-not-save"})
            first = _paid_audio(store, paid_config(), story, {"kind": "music"}, root, .4, callback)
            second = _paid_audio(store, paid_config(), story, {"kind": "music"}, root, .4,
                                 lambda: self.fail("Completed resource must not be regenerated"))
            self.assertEqual(first[0], second[0])
            self.assertNotIn("do-not-save", (root / "response-headers.json").read_text())

    def test_provider_response_tampering_blocks_reuse(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            story = {"story_id": "story", "budget": {"limit": 1, "currency": "EUR"}}
            _paid_audio(store, paid_config(), story, {"kind": "tts"}, root, .4,
                        lambda: (b"received", {"content-type": "audio/mpeg"}))
            (root / "response.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "provider_response_changed"):
                _paid_audio(store, paid_config(), story, {"kind": "tts"}, root, .4,
                            lambda: self.fail("Must not regenerate a paid resource"))


class ClientTests(unittest.TestCase):
    def client(self, calls):
        def transport(method, path, body):
            if path == "/v1/models":
                value = [{"model_id": "test-model", "can_do_text_to_speech": True, "maximum_text_length_per_request": 5000}]
            elif path == "/v1/user/subscription":
                value = {"tier": "starter", "status": "active", "open_invoices": ["private"]}
            elif path.startswith("/v2/voices"):
                value = {"voices": [{"voice_id": "test-voice", "name": "Narrateur"}], "has_more": False}
            else:
                calls.append((method, path, body))
                value = {"audio_base64": base64.b64encode(wav_bytes()).decode(), "alignment": {
                    "characters": list(body.get("text", "a")),
                    "character_start_times_seconds": [0.] * len(body.get("text", "a")),
                    "character_end_times_seconds": [.1] * len(body.get("text", "a"))}}
            return json.dumps(value).encode(), {"content-type": "application/json"}
        return ElevenLabsClient(transport=transport)

    def test_dialogue_is_one_mix_and_keeps_provider_segments(self):
        body = json.dumps({"audio_base64": base64.b64encode(wav_bytes()).decode(), "voice_segments": [
            {"voice_id": "a", "dialogue_input_index": 0, "start_time_seconds": 0, "end_time_seconds": .2}]}).encode()
        audio, metadata = parse_audio_response(body, "application/json")
        self.assertEqual(audio, wav_bytes())
        self.assertEqual(metadata["voice_segments"][0]["dialogue_input_index"], 0)
        self.assertNotIn("stems", metadata)

    def test_music_mime_is_parsed_and_plan_does_not_include_prompt_parameters(self):
        body = b'--boundary\r\nContent-Type: application/json\r\n\r\n{"composition_plan":{}}\r\n--boundary\r\nContent-Type: audio/mpeg\r\n\r\nAUDIO\r\n--boundary--\r\n'
        audio, details = parse_audio_response(body, 'multipart/mixed; boundary="boundary"')
        self.assertEqual(audio, b"AUDIO")
        self.assertIn("composition_plan", details)
        calls = []
        client = self.client(calls)
        plan = {"positive_global_styles": ["instrumental"], "negative_global_styles": [], "sections": [
            {"section_name": "Theme", "duration_ms": 600000, "positive_local_styles": [], "negative_local_styles": [], "lines": []}]}
        client.music(model_id="music_v1", composition_plan=plan)
        value = calls[-1][2]
        self.assertNotIn("force_instrumental", value)
        self.assertNotIn("music_length_ms", value)
        self.assertNotIn("prompt", value)

    def test_composition_duration_cannot_underreserve_budget(self):
        plan = {"positive_global_styles": ["instrumental"], "negative_global_styles": [], "sections": [
            {"section_name": "Theme", "duration_ms": 600000, "positive_local_styles": [], "negative_local_styles": [], "lines": []}]}
        music = {"provider": "elevenlabs", "composition_plan": plan, "duration_seconds": 3}
        script = {"scenes": [{"sound": {"music": music}}]}
        config = {"storytelling": {"elevenlabs": {"cost_per_music_second_upper_bound": 1, "currency": "EUR"}}}
        with self.assertRaisesRegex(ValueError, "duration_mismatch"):
            estimate_audio(script, config)
        del music["duration_seconds"]
        self.assertEqual(estimate_audio(script, config)["amount_upper_bound"], 600)
        music["prompt"] = "instrumental"
        with self.assertRaisesRegex(ValueError, "prompt_or_plan"):
            estimate_audio(script, config)

    def test_model_or_voice_unavailable_blocks_before_post(self):
        calls = []
        client = self.client(calls)
        with self.assertRaises(ProviderError):
            client.tts("Texte", "unknown", "test-model")
        self.assertEqual(calls, [])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_truncated_alignment_blocks_without_second_paid_generation(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            calls = []
            client = self.client(calls)
            original = client.transport
            def truncated(method, path, body):
                data, headers = original(method, path, body)
                if method == "POST":
                    value = json.loads(data)
                    value["alignment"] = {"characters": ["a"], "character_start_times_seconds": [0.], "character_end_times_seconds": [.1]}
                    data = json.dumps(value).encode()
                return data, headers
            client.transport = truncated
            script = {"story_id": "story", "budget": {"limit": 10, "currency": "EUR"}, "speakers": {
                "n": {"voice": {"provider": "elevenlabs", "authorization": "fixture", "voice_id": "test-voice", "model_id": "test-model"}}},
                "scenes": [{"scene_id": "s", "utterances": [{"utterance_id": "u", "speaker_id": "n", "text": "Un paragraphe complet doit être prononcé."}]}]}
            with patch("youtube_growth.factory.storytelling_audio.ElevenLabsClient", return_value=client):
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError, "text_coverage_mismatch"):
                        produce_audio(store, paid_config(), script, Path(directory) / "output")
            self.assertEqual(len([c for c in calls if c[0] == "POST"]), 1)
            row = store.records("storytelling_audio_call")[0]
            self.assertEqual(row["status"], "completed")
            self.assertTrue(row["response_sha256"])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_only_spoken_text_is_sent_and_cached(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            calls = []
            script = {"story_id": "story", "budget": {"limit": 10, "currency": "EUR"}, "speakers": {
                "narrator": {"name": "NE DOIT PAS ETRE LU", "voice": {"provider": "elevenlabs", "authorization": "fixture",
                    "voice_id": "test-voice", "model_id": "test-model"}}}, "scenes": [{"scene_id": "opening", "utterances": [
                        {"utterance_id": "u1", "speaker_id": "narrator", "text": "Une phrase.", "delivery": {"emotion": "curieux", "intention": "ne pas lire"}}]}]}
            client = self.client(calls)
            with patch("youtube_growth.factory.storytelling_audio.ElevenLabsClient", return_value=client):
                first = produce_audio(store, paid_config(), script, Path(directory) / "output")
                second = produce_audio(store, paid_config(), script, Path(directory) / "output2")
            posts = [c for c in calls if c[0] == "POST"]
            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0][2]["text"], "Une phrase.")
            self.assertAlmostEqual(first["duration_seconds"], .2)
            self.assertEqual(first["scenes"][0]["utterances"][0]["sha256"], second["scenes"][0]["utterances"][0]["sha256"])


class RecordingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_imported_caption_bounds_and_text_coverage_are_checked(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            source = root / "source.wav"
            source.write_bytes(wav_bytes(.4))
            recording = {"path": str(source), "sha256": fingerprint(source), "caption_segments": [
                {"text": "Une phrase.", "start_seconds": 0, "end_seconds": .2},
                {"text": "La suite.", "start_seconds": .2, "end_seconds": .4}]}
            script = {"story_id": "story", "speakers": {"n": {"voice": {"provider": "recordings", "authorization": "fixture", "recordings": {"u": recording}}}},
                      "scenes": [{"scene_id": "s", "utterances": [{"utterance_id": "u", "speaker_id": "n", "text": "Une phrase. La suite."}]}]}
            result = produce_audio(store, {}, script, root / "first")
            self.assertEqual(result["scenes"][0]["utterances"][0]["caption_segments"], recording["caption_segments"])
            recording["caption_segments"][1]["text"] = "Une phrase."
            with self.assertRaisesRegex(ValueError, "caption_coverage_invalid"):
                produce_audio(store, {}, script, root / "second")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_system_captions_use_measured_chunk_files_and_reuse_unchanged_lines(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            calls = []
            def system(text, voice, path):
                calls.append(text)
                target = path / "system.wav"
                target.write_bytes(wav_bytes(.2))
                return target
            long_text = "Une explication longue avance avec des observations précises et garde les repères nécessaires pour comprendre la suite. " * 4
            script = {"story_id": "story", "speakers": {"n": {"voice": {"provider": "system", "name": "Fixture", "authorization": "fixture"}}},
                      "scenes": [{"scene_id": "s", "utterances": [
                          {"utterance_id": "a", "speaker_id": "n", "text": long_text},
                          {"utterance_id": "b", "speaker_id": "n", "text": "La conclusion reste courte."}]}]}
            with patch("youtube_growth.factory.storytelling_audio._system", side_effect=system):
                first = produce_audio(store, {}, script, root / "first")
                initial_count = len(calls)
                repeated = produce_audio(store, {}, script, root / "repeated")
                self.assertEqual(len(calls), initial_count)
                line = first["scenes"][0]["utterances"][0]
                self.assertGreater(len(line["caption_segments"]), 1)
                self.assertTrue(all(len(c["text"]) <= 150 for c in line["caption_segments"]))
                self.assertAlmostEqual(line["caption_segments"][-1]["end_seconds"], line["duration_seconds"])
                self.assertAlmostEqual(line["caption_segments"][0]["end_seconds"], .2)
                script["scenes"][0]["utterances"][0]["text"] = "Une correction brève."
                revised = produce_audio(store, {}, script, root / "revised")
                self.assertEqual(len(calls), initial_count + 1)
                self.assertEqual(first["scenes"][0]["utterances"][1]["path"], revised["scenes"][0]["utterances"][1]["path"])
                self.assertAlmostEqual(revised["scenes"][0]["utterances"][1]["start_seconds"], .2)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_revision_reuses_unchanged_utterances_and_recalculates_times(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            root = Path(directory)
            a, b, c = (root / name for name in ("a.wav", "b.wav", "c.wav"))
            a.write_bytes(wav_bytes(.2)); b.write_bytes(wav_bytes(.3)); c.write_bytes(wav_bytes(.6))
            def recording(path):
                return {"path": str(path), "sha256": fingerprint(path)}
            script = {"story_id": "story", "speakers": {"n": {"voice": {"provider": "recordings", "authorization": "fixture",
                       "recordings": {"a": recording(a), "b": recording(b)}}}}, "scenes": [{"scene_id": "s", "utterances": [
                           {"utterance_id": "a", "speaker_id": "n", "text": "A"}, {"utterance_id": "b", "speaker_id": "n", "text": "B"}]}]}
            first = produce_audio(store, {}, script, root / "first")
            script["speakers"]["n"]["voice"]["recordings"]["a"] = recording(c)
            second = produce_audio(store, {}, script, root / "second")
            # Mapping for a different utterance must not invalidate b's cache key.
            self.assertAlmostEqual(second["scenes"][0]["utterances"][1]["start_seconds"], .6)
            self.assertEqual(first["scenes"][0]["utterances"][1]["sha256"], second["scenes"][0]["utterances"][1]["sha256"])
            self.assertEqual(first["scenes"][0]["utterances"][1]["path"], second["scenes"][0]["utterances"][1]["path"])

    def test_long_text_split_respects_limit_without_technical_tags(self):
        self.assertEqual(split_text("Une phrase assez longue", 10), ["Une phrase", "assez", "longue"])


if __name__ == "__main__":
    unittest.main()
