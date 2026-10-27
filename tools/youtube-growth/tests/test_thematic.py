from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.thematic import quantize, run
from youtube_growth.thematic_analysis import analyze_local, analyze_openai
from youtube_growth.thematic_core import edit_timeline, read_transcript, sentences, subtitles, validate_analysis, validate_transcript
from youtube_growth.thematic_render import canvas


def fixture():
    units = [{"start": i*10.0, "end": (i+1)*10.0, "text": f"Phrase complète numéro {i}."} for i in range(33)]
    candidate = {"topic": "Contexte des agents", "title": "Comment conserver le contexte des agents ?",
                 "description": "Nous discutons de la gestion du contexte.", "thumbnail_text": "Le contexte des agents",
                 "rationale": "Question, exemples et conclusion sont conservés.",
                 "scores": dict.fromkeys(("audience", "discussion", "standalone", "hook", "substance", "retention"), 80),
                 "ranges": [[0, 9], [11, 30]], "hook": [3, 3],
                 "evidence": {role: {"index": i, "quote": units[i]["text"]} for role, i in
                              (("question", 0), ("development", 20), ("conclusion", 30))}}
    return units, {"candidates": [candidate]}


class ThematicCoreTests(unittest.TestCase):
    def setUp(self):
        self.units, self.raw = fixture()

    def test_no_quota_and_no_invented_candidates(self):
        self.assertEqual(validate_analysis({"candidates": []}, self.units)["selected"], [])
        self.assertEqual(analyze_local(self.units), {"candidates": []})

    def test_rejects_invalid_or_unordered_transcripts(self):
        for rows in ([{"start": float("nan"), "end": 20, "text": "x"}],
                     [{"start": 10, "end": 20, "text": "x"}, {"start": 19, "end": 22, "text": "x"}],
                     [{"start": 0, "end": 331, "text": "x"}], [{"start": True, "end": 2, "text": "x"}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                validate_transcript(rows, 330)

    def test_reuses_shorts_manifest_and_jsonl_without_modification(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            raw = json.dumps({"segments": self.units, "clips": [{"youtube_video_id": "existing"}]})
            path.write_text(raw, encoding="utf-8")
            self.assertEqual(read_transcript(path, 330), self.units)
            self.assertEqual(path.read_text(encoding="utf-8"), raw)
            jsonl = path.with_suffix(".jsonl")
            jsonl.write_text("\n".join(json.dumps(row) for row in self.units), encoding="utf-8")
            self.assertEqual(read_transcript(jsonl, 330), self.units)
            path.write_text(json.dumps({"source_video_id": "wrong", "segments": self.units}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "autre épisode"):
                read_transcript(path, 330, "GgSiPkADCz4")

    def test_merges_fragments_and_preserves_speech_before_editing(self):
        rows = [{"start": 0, "end": 3, "text": "Une phrase"}, {"start": 3, "end": 7, "text": "qui finit ici."}]
        self.assertEqual(sentences(rows), [{"start": 0, "end": 7, "text": "Une phrase qui finit ici."}])

    def test_scores_rank_and_deduplicate_shared_source(self):
        second = copy.deepcopy(self.raw["candidates"][0])
        second["topic"] = "Un autre angle similaire"
        second["scores"] = dict.fromkeys(second["scores"], 95)
        self.raw["candidates"].append(second)
        result = validate_analysis(self.raw, self.units)
        self.assertEqual(result["selected"][0]["score"], 95)
        self.assertEqual(len(result["selected"]), 1)
        self.assertIn("déjà utilisées", result["rejected"][0]["rejection_reason"])

    def test_weak_topics_are_rejected_even_if_duration_fits(self):
        self.raw["candidates"][0]["scores"]["standalone"] = 20
        self.assertEqual(validate_analysis(self.raw, self.units)["selected"], [])

    def test_rejects_invented_or_missing_narrative_evidence(self):
        for mutation in ("quote", "order", "missing", "end"):
            raw = copy.deepcopy(self.raw)
            evidence = raw["candidates"][0]["evidence"]
            if mutation == "quote":
                evidence["question"]["quote"] = "Des paroles jamais prononcées."
            elif mutation == "order":
                evidence["development"] = evidence["question"]
            elif mutation == "missing":
                del evidence["conclusion"]
            else:
                evidence["conclusion"] = {"index": 29, "quote": self.units[29]["text"]}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_analysis(raw, self.units)

    def test_rejects_disordered_out_of_range_and_boolean_indices(self):
        for ranges in ([[0, 10000]], [[10, 15], [5, 30]], [[False, 30]], [[0, 10], [10, 30]]):
            raw = copy.deepcopy(self.raw)
            raw["candidates"][0]["ranges"] = ranges
            with self.subTest(ranges=ranges), self.assertRaises(ValueError):
                validate_analysis(raw, self.units)

    def test_enforces_hook_duration_and_source_membership(self):
        for hook in ([3, 5], [-1, -1], [10, 10], [32, 32], [True, 3]):
            raw = copy.deepcopy(self.raw)
            raw["candidates"][0]["hook"] = hook
            with self.subTest(hook=hook), self.assertRaises(ValueError):
                validate_analysis(raw, self.units)

    def test_rejects_invalid_scores_titles_and_thumbnail_copy(self):
        for key, value in (("title", "x"*101), ("thumbnail_text", "Un"), ("scores", {"audience": 80})):
            raw = copy.deepcopy(self.raw)
            raw["candidates"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_analysis(raw, self.units)

    def test_includes_hook_in_total_duration(self):
        raw = copy.deepcopy(self.raw)
        raw["candidates"][0]["ranges"] = [[0, 28]]
        raw["candidates"][0]["evidence"]["conclusion"] = {"index": 28, "quote": self.units[28]["text"]}
        self.assertEqual(validate_analysis(raw, self.units)["selected"][0]["duration_before_silence_trim"], 300)
        self.units[28]["end"] = 289
        with self.assertRaises(ValueError):
            validate_analysis(raw, self.units)

    def test_cut_map_retimes_subtitles_including_replayed_hook(self):
        candidate = validate_analysis(self.raw, self.units)["selected"][0]
        timeline = edit_timeline(candidate, self.units, self.units)
        self.assertEqual(timeline[-1]["output_end"], 310)
        self.assertEqual(timeline[0]["source_start"], 30)
        self.assertEqual(timeline[1]["source_start"], 0)
        self.assertEqual(timeline[2]["source_start"], 110)
        srt = subtitles(timeline, self.units)
        self.assertIn("00:00:00,000 --> 00:00:10,000", srt)
        self.assertEqual(srt.count("Phrase complète numéro 3."), 2)
        self.assertNotIn("Phrase complète numéro 10.", srt)
        self.assertIn("00:05:00,000 --> 00:05:10,000", srt)

    def test_removes_only_long_untranscribed_gaps_with_breathing_room(self):
        segments = copy.deepcopy(self.units)
        segments[5]["end"] = 56
        candidate = validate_analysis(self.raw, self.units)["selected"][0]
        timeline = edit_timeline(candidate, self.units, segments)
        self.assertAlmostEqual(timeline[-1]["output_end"], 306.36)
        self.assertTrue(any(e["source_end"] == 56.18 for e in timeline))
        self.assertTrue(any(e["source_start"] == 59.82 for e in timeline))

    def test_frame_alignment_never_accumulates_subtitle_drift(self):
        timeline = [{"source_start": i*2, "source_end": i*2+1.017, "role": "body"} for i in range(310)]
        quantize(timeline, "30000/1001")
        expected = sum(e["frames"] for e in timeline) / (30000/1001)
        self.assertAlmostEqual(timeline[-1]["output_end"], expected, places=5)

    def test_canvas_preserves_source_resolution_without_forced_1080_upscale(self):
        info = {"streams": [{"codec_type": "video", "width": 1280, "height": 720, "r_frame_rate": "25/1"}, {"codec_type": "audio"}]}
        self.assertEqual(canvas(info), (1280, 720, "25/1"))
        info["streams"][0].update(width=1920, height=1080)
        self.assertEqual(canvas(info)[:2], (1920, 1080))

    def test_openai_is_explicit_and_does_not_leak_error_bodies(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(ValueError):
            analyze_openai(self.units, "")
        from urllib.error import HTTPError
        api_error = HTTPError("https://example.invalid", 429, "private-body", {}, None)
        self.addCleanup(api_error.close)
        with patch.dict("os.environ", {"OPENAI_API_KEY": "never-print-me"}), patch("youtube_growth.thematic_analysis.urlopen", side_effect=api_error):
            with self.assertRaisesRegex(RuntimeError, "429") as error:
                analyze_openai(self.units, "configured-model")
            self.assertNotIn("private-body", str(error.exception))
            self.assertNotIn("never-print-me", str(error.exception))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and importlib.util.find_spec("PIL"), "FFmpeg, ffprobe et Pillow requis pour la recette média")
class ThematicMediaTests(unittest.TestCase):
    def test_real_ffmpeg_export_cache_integrity_and_shorts_isolation(self):
        units, raw = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=3:duration=330",
                            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=330",
                            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(source)], check=True, capture_output=True)
            transcript, analysis = root / "transcript.json", root / "analysis.json"
            transcript.write_text(json.dumps(units), encoding="utf-8")
            analysis.write_text(json.dumps(raw), encoding="utf-8")
            shorts = root / "shorts"
            shorts.mkdir()
            original = b'{"clips":[{"youtube_video_id":"already-uploaded"}]}'
            (shorts / "manifest.json").write_bytes(original)
            with self.assertRaisesRegex(ValueError, "non vide"):
                run(source, transcript, shorts, analysis=analysis)
            self.assertEqual((shorts / "manifest.json").read_bytes(), original)
            output = root / "thematic"
            first = run(source, transcript, output, analysis=analysis)
            self.assertEqual(first["videos"], 1)
            manifest = json.loads((output / "thematic-manifest.json").read_text(encoding="utf-8"))
            record = manifest["videos"][0]
            self.assertEqual(record["technical"]["status"], "decoded")
            self.assertAlmostEqual(record["technical"]["duration"], 310, delta=.1)
            self.assertLess(record["technical"]["av_duration_delta"], .15)
            directory = output / record["folder"]
            from PIL import Image
            with Image.open(directory / "thumbnail.png") as image:
                self.assertEqual(image.size, (1280, 720))
            mtime = (directory / "video.mp4").stat().st_mtime_ns
            with patch("youtube_growth.thematic.analyze_local", side_effect=AssertionError("Cache non réutilisé")):
                second = run(source, transcript, output, analysis=analysis)
            self.assertEqual(second["status"], "complete")
            self.assertEqual((directory / "video.mp4").stat().st_mtime_ns, mtime)
            burned = root / "burned"
            self.assertEqual(run(source, transcript, burned, analysis=analysis, burn=True)["videos"], 1)
            from youtube_growth.thematic_render import probe
            burned_video = next(burned.glob("video-*/video.mp4"))
            self.assertFalse(any(s["codec_type"] == "subtitle" for s in probe(burned_video, "ffprobe")["streams"]))
            with self.assertRaisesRegex(ValueError, "paramètres différents"):
                run(source, transcript, output, analysis=analysis, count=1)
            (directory / "video.mp4").write_bytes(b"broken-output")
            with self.assertRaisesRegex(ValueError, "export final a été modifié"):
                run(source, transcript, output, analysis=analysis)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "NumPy requis pour la comparaison source")
class ThematicCorrespondenceTests(unittest.TestCase):
    def test_audio_gain_is_not_mistaken_for_desynchronization_and_silence_is_unverifiable(self):
        import numpy as np
        from youtube_growth.thematic_qa import correlation
        signal = np.random.default_rng(2).normal(size=8000)
        self.assertAlmostEqual(correlation(signal, signal*12+.5), 1)
        self.assertIsNone(correlation(signal, np.zeros(8000)))

    def test_content_comparison_detects_shifted_sound_and_replaced_picture(self):
        import numpy as np
        from youtube_growth.thematic_qa import compare
        signal = np.random.default_rng(5).normal(size=4000*30).astype("<f4")
        picture = np.random.default_rng(8).integers(0, 255, size=128*72, dtype=np.uint8)
        timeline = [{"source_start": 10, "source_end": 20, "output_start": 0, "output_end": 10}]
        def fake(shift=0, wrong_picture=False):
            def media(_ffmpeg, path, time, audio, duration=2):
                if not audio:
                    return (255-picture if wrong_picture and path.name == "video.mp4" else picture).tobytes()
                time += 10+shift if path.name == "video.mp4" else 0
                index = round(time*4000)
                return signal[index:index+round(duration*4000)].tobytes()
            return media
        for shift, wrong_picture, expected in ((0, False, "source_correspondence_verified"), (.04, False, "needs_review"), (0, True, "needs_review")):
            with patch("youtube_growth.thematic_qa.media_bytes", side_effect=fake(shift, wrong_picture)):
                self.assertEqual(compare(Path("source.mp4"), Path("video.mp4"), timeline, "ffmpeg")["status"], expected)


if __name__ == "__main__":
    unittest.main()
