"""Opt-in media recipe with synthetic tones, never an editorial listening review."""
import math
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from youtube_growth.factory.media import probe
from youtube_growth.factory import storytelling_render
from youtube_growth.factory.storytelling_render import artifact, build_timeline, render


def tone(path, duration, frequency, gain=.15):
    rate = 48000
    samples = bytearray()
    for i in range(round(duration * rate)):
        # Short edge fades prevent fixture clicks from dominating the peak check.
        envelope = min(1, i / (rate * .025), (duration * rate - i) / (rate * .025))
        samples.extend(struct.pack("<h", round(32767 * gain * envelope * math.sin(2 * math.pi * frequency * i / rate))))
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(samples)


class StorytellingPosterTests(unittest.TestCase):
    def test_image_fills_the_frame_and_scene_function_never_becomes_a_title(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "square.png"
            Image.new("RGB", (400, 400), (220, 30, 30)).save(source)
            shot = {"type": "image", "source": {"path": str(source)}, "factual_status": "fact",
                    "heading": "Note interne de la scène"}
            storytelling_render.poster(shot, root / "with-heading.png", (960, 540))
            storytelling_render.poster({**shot, "heading": "Autre note"}, root / "other-heading.png", (960, 540))
            with Image.open(root / "with-heading.png") as first, Image.open(root / "other-heading.png") as second:
                self.assertEqual(first.tobytes(), second.tobytes())
                self.assertEqual(first.getpixel((480, 270)), (220, 30, 30))
                # The sides show a blurred copy of the picture, not the old dark card background.
                red, green, blue = first.getpixel((40, 270))
                self.assertGreater(red, green + 40)


@unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1", "Recette média explicite requise")
@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg et FFprobe requis")
class StorytellingRenderIntegrationTests(unittest.TestCase):
    def test_real_mix_subtitles_and_global_frame_quantization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            voice, music, effect = (root / name for name in ("synthetic-voice.wav", "synthetic-music.wav", "synthetic-effect.wav"))
            duration = 3.1
            tone(voice, duration, 440, .20)
            tone(music, duration, 220, .12)
            tone(effect, .35, 880, .18)
            utterances = [
                {"utterance_id": "u1", "speaker_id": "n", "text": "Premier repère synthétique."},
                {"utterance_id": "u2", "speaker_id": "n", "text": "Deuxième repère synthétique."},
                {"utterance_id": "u3", "speaker_id": "n", "text": "Dernier repère de cette recette technique."}]
            boundaries = (0., .46, .92, duration)
            script = {"story_id": "synthetic-render-recipe", "synthetic": True, "scenes": [{
                "scene_id": "s", "function": "Contrôler le montage local", "factual_status": "fiction",
                "utterances": utterances, "shots": [
                    {"shot_id": "shot-" + str(i), "type": "diagram", "utterance_ids": [u["utterance_id"]],
                     "description": "Repère technique synthétique " + str(i + 1), "labels": ["Recette technique", "Aucun propos réel"],
                     "on_screen_text": "Plan " + str(i + 1)} for i, u in enumerate(utterances)]}]}
            audio = {"scenes": [{"scene_id": "s", "start_seconds": 0., "duration_seconds": duration, **artifact(voice),
                                 "utterances": [{**u, "start_seconds": boundaries[i], "end_seconds": boundaries[i + 1]}
                                                for i, u in enumerate(utterances)]}],
                     "duration_seconds": duration, "synthetic": True,
                     "sound_tracks": [{**artifact(music), "kind": "music", "start_seconds": 0., "duration_seconds": duration, "level_db": -18},
                                      {**artifact(effect), "kind": "effect", "start_seconds": 1.2, "duration_seconds": .35, "gain_db": -10}],
                     "artifacts": [artifact(voice), artifact(music), artifact(effect)]}
            timeline = build_timeline(script, audio, [])
            self.assertEqual(timeline["clock"], "measured_audio")
            self.assertEqual(len(timeline["shots"]), 3)
            self.assertAlmostEqual(timeline["captions"][1]["start_seconds"], .46)
            self.assertEqual(len(timeline["sound_tracks"]), 2)
            # These chosen durations expose drift if each shot is rounded in isolation.
            self.assertNotEqual(sum(round(s["duration_seconds"] * 12) for s in timeline["shots"]), round(duration * 12))
            calls = []
            original = storytelling_render._run
            def spy(args):
                calls.append(args)
                return original(args)
            with patch("youtube_growth.factory.storytelling_render._run", side_effect=spy):
                result = render(script, timeline, audio, root / "export", draft=True)
            # The documented level_db reaches the mix, like a legacy gain_db.
            mix = calls[-1][calls[-1].index("-filter_complex") + 1]
            self.assertIn("volume=-18.0dB", mix)
            self.assertIn("volume=-10.0dB", mix)
            info = probe(Path(result["path"]))
            inspection = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-count_frames", "-show_streams", "-of", "json", result["path"]],
                                        capture_output=True, timeout=30, check=True)
            streams = json.loads(inspection.stdout)["streams"]
            video = next(s for s in streams if s["codec_type"] == "video")
            speech = next(s for s in streams if s["codec_type"] == "audio")
            subtitles = next(s for s in streams if s["codec_type"] == "subtitle")
            self.assertEqual(video["codec_name"], "h264")
            self.assertEqual(int(video["nb_read_frames"]), round(duration * 12))
            self.assertEqual(speech["codec_name"], "aac")
            self.assertEqual(int(speech["sample_rate"]), 48000)
            self.assertEqual(subtitles["codec_name"], "mov_text")
            self.assertEqual(subtitles.get("tags", {}).get("language"), "fra")
            self.assertAlmostEqual(info["duration_seconds"], duration, delta=.15)
            self.assertEqual(result["technical"]["decode"], "passed")
            peak = result["technical"]["max_volume_db"]
            self.assertIsNotNone(peak)
            self.assertGreater(peak, -25)
            self.assertLess(peak, 0)
            extracted = subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-i", result["path"], "-map", "0:s:0", "-f", "srt", "-"],
                                       capture_output=True, timeout=30, check=True).stdout.decode("utf-8-sig")
            self.assertIn("Premier repère synthétique.", extracted)
            self.assertIn("Dernier repère de cette recette technique.", extracted)
            self.assertIn("00:00:00,460", extracted)
            self.assertTrue(Path(result["vtt"]).read_text(encoding="utf-8").startswith("WEBVTT"))


if __name__ == "__main__":
    unittest.main()
