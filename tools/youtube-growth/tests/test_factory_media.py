"""Media provenance and local simulation boundaries, without paid calls."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from youtube_growth.factory import media
from youtube_growth.factory.local_lock import local_lock


class ProcessLockTests(unittest.TestCase):
    def test_process_death_releases_lock_without_unlinking_the_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "from pathlib import Path; import sys,time; from youtube_growth.factory.local_lock import local_lock; " \
                     "lock=local_lock(Path(sys.argv[1])); lock.__enter__(); print('locked',flush=True); time.sleep(60)"
            environment = {**os.environ, "PYTHONPATH": os.pathsep.join(str(Path(p).resolve()) for p in sys.path if p)}
            child = subprocess.Popen([sys.executable, "-u", "-c", script, str(root)], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, env=environment)
            try:
                self.assertEqual(child.stdout.readline().strip(), "locked")
                inode = (root / "run.lock").stat().st_ino
                with self.assertRaises(RuntimeError):
                    with local_lock(root):
                        self.fail("Deux processus ont obtenu le verrou.")
                child.terminate()
                child.wait(timeout=10)
                with local_lock(root):
                    self.assertEqual((root / "run.lock").stat().st_ino, inode)
                self.assertTrue((root / "run.lock").exists())
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=10)
                child.stdout.close()
                child.stderr.close()


class InterruptedRenderTests(unittest.TestCase):
    def test_restart_reuses_finished_stages_after_quality_scan_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            source.write_bytes(b"owned-source")
            candidate = {"start_seconds": 0, "end_seconds": 12, "title": "Version initiale"}
            def probe(path):
                final = path.name == "video.mp4"
                return {"duration_seconds": 12 if final else 100,
                        "streams": [{"codec_type": "video", "codec_name": "h264", "duration": "12",
                                     "width": 1080 if final else 640, "height": 1920 if final else 360},
                                    {"codec_type": "audio", "codec_name": "aac", "duration": "12"}]}
            def encode(arguments):
                Path(arguments[-1]).write_bytes(b"encoded-stage")
                return ""
            with patch.object(media, "probe", side_effect=probe), \
                 patch.object(media, "_call", side_effect=encode), \
                 patch.object(media, "_scan", side_effect=RuntimeError("interrupted_scan")):
                with self.assertRaisesRegex(RuntimeError, "interrupted_scan"):
                    media.render(source, candidate, root / "renders", fixture=True)
            completed = list((root / "renders").glob("*/master-clean.mp4"))[0]
            original_time = completed.stat().st_mtime_ns
            technical = {"decode": "passed", "black_intervals_seconds": [], "silence_events": [], "max_volume_db": -3.0}
            with patch.object(media, "probe", side_effect=probe), patch.object(media, "_call") as encoder, \
                 patch.object(media, "_scan", return_value=technical), patch.object(media, "_frames", return_value=[]):
                result = media.render(source, {**candidate, "title": "Titre corrigé"}, root / "renders", fixture=True)
                encoder.assert_not_called()
            self.assertEqual(completed.stat().st_mtime_ns, original_time)
            self.assertEqual(result["qa"]["technical"], "passed")


class MediaPureTests(unittest.TestCase):
    def test_cuts_keep_source_and_output_correspondence(self):
        candidate = {"cuts": [{"source_start_seconds": 10, "source_end_seconds": 20},
                               {"source_start_seconds": 40, "source_end_seconds": 55}]}
        cuts = media._cuts(candidate, 80)
        self.assertEqual([(r["output_start_seconds"], r["output_end_seconds"]) for r in cuts], [(0, 10), (10, 25)])
        self.assertEqual(cuts[1]["source_start_seconds"], 40)

    def test_overlaps_reordering_non_finite_and_missing_cuts_fail(self):
        bad = [{"start_seconds": 0, "end_seconds": float("nan")},
               {"start_seconds": True, "end_seconds": 8},
               {"cuts": [{"source_start_seconds": 5, "source_end_seconds": 10},
                         {"source_start_seconds": 9, "source_end_seconds": 15}]},
               {"start_seconds": 0, "end_seconds": 100}]
        for candidate in bad:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                media._cuts(candidate, 20)

    def test_coverage_unions_overlaps_and_preserves_unexamined_ranges(self):
        result = media._coverage([[0, 3], [2, 4], [6, 8]], 10)
        self.assertEqual(result["covered_seconds"], 6)
        self.assertEqual(result["unexamined_ranges_seconds"], [[4, 6], [8, 10]])
        self.assertFalse(result["complete"])
        self.assertFalse(media._covered([[0, 4], [6, 8]], 3, 7))

    def test_subtitles_rebase_multi_cut_and_preserve_words(self):
        segments = [{"start": 0, "end": 8, "text": "Mots hors du montage."},
                    {"start": 10, "end": 15, "text": "OpenAI GPT, QA et product management."},
                    {"start": 40, "end": 44, "text": "La réserve reste présente."}]
        cuts = media._cuts({"cuts": [{"source_start_seconds": 10, "source_end_seconds": 20},
                                     {"source_start_seconds": 40, "source_end_seconds": 50}]}, 60)
        result = media._subtitles(segments, cuts)
        self.assertIn("00:00:00,000 --> 00:00:05,000", result)
        self.assertIn("00:00:10,000 --> 00:00:14,000", result)
        self.assertIn("OpenAI GPT, QA et product management.", result)
        self.assertNotIn("hors du montage", result)

    def test_cut_inside_a_transcript_segment_does_not_show_unheard_words(self):
        cuts = media._cuts({"start_seconds": 3, "end_seconds": 8}, 20)
        result = media._subtitles([{"start": 0, "end": 10, "text": "Une phrase dont seule une partie est conservée."}], cuts)
        self.assertEqual(result, "")


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"owned-source")
        self.transcript = self.root / "transcript.json"
        self.transcript.write_text(json.dumps({"source_sha256": media.fingerprint(self.source),
                                              "segments": [{"start": 0, "end": 100, "text": "Toute la transcription fournie."}]}), encoding="utf-8")
        self.evidence = self.root / "evidence.json"
        self.info = {"duration_seconds": 100, "streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}

    def evidence_value(self):
        return {"version": 1, "source_sha256": media.fingerprint(self.source),
                "provenance": {"kind": "human_review", "reviewer": "test-reviewer", "prompt_version": "test-v1"},
                "coverage": {k+"_ranges_seconds": [[0, 100]] for k in ("audio", "visual", "transcript")},
                "candidates": [{"title": "Sujet concret", "audience": "Développeurs", "rationale": "Explication autonome.",
                                "start_seconds": 10, "end_seconds": 30, "decision": "retained"}]}

    def run_analysis(self, evidence=None):
        with patch.object(media, "probe", return_value=self.info), \
             patch.object(media, "_scan", return_value={"decode": "passed"}), \
             patch.object(media, "_frames", return_value=[]):
            return media.analyze(self.source, self.transcript, self.root / "analysis", evidence=evidence)

    def test_no_model_does_not_invent_candidates_or_multimodal_review(self):
        result = self.run_analysis()
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["coverage"]["transcript"]["segments_read"], 1)
        self.assertEqual(result["coverage"]["audio"]["technical"], "complete")
        self.assertFalse(result["coverage"]["visual"]["semantic_review"]["complete"])
        self.assertTrue(result["blockers"])

    def test_partial_visual_review_overrides_retained_decision(self):
        value = self.evidence_value()
        value["coverage"]["visual_ranges_seconds"] = [[0, 20]]
        self.evidence.write_text(json.dumps(value), encoding="utf-8")
        result = self.run_analysis(self.evidence)
        self.assertEqual(result["candidates"][0]["decision"], "needs_review")
        self.assertEqual(result["coverage"]["visual"]["semantic_review"]["unexamined_ranges_seconds"], [[20, 100]])

    def test_mismatched_source_evidence_is_rejected(self):
        value = self.evidence_value()
        value["source_sha256"] = "wrong-source"
        self.evidence.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_analysis(self.evidence)

    def test_bad_candidate_is_isolated_from_valid_candidate(self):
        value = self.evidence_value()
        value["candidates"].append({"title": "Hors source", "start_seconds": 90, "end_seconds": 130})
        self.evidence.write_text(json.dumps(value), encoding="utf-8")
        result = self.run_analysis(self.evidence)
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["decision"], "retained")
        self.assertEqual(len(result["rejected_inputs"]), 1)

    def test_cached_analysis_reuses_full_audio_scan(self):
        result = self.run_analysis()
        with patch.object(media, "probe", return_value=self.info), patch.object(media, "_scan") as scanner:
            again = media.analyze(self.source, self.transcript, self.root / "analysis")
        self.assertEqual(result["cache_key"], again["cache_key"])
        scanner.assert_not_called()


@unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1", "Activer FACTORY_MEDIA_INTEGRATION=1 pour les rendus FFmpeg.")
class RealMediaTests(unittest.TestCase):
    def test_fixture_short_and_long_decode_and_reuse_immutable_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = media.create_fixture(root / "input")
            source, transcript = Path(fixture["source"]), Path(fixture["transcript"])
            analysis = media.analyze(source, transcript, root / "analysis", evidence=Path(fixture["evidence"]))
            assets = [media.render(source, c, root / "renders", format=c["format"], transcript=transcript, fixture=True)
                      for c in analysis["candidates"]]
            self.assertEqual([round(a["duration_seconds"]) for a in assets], [12, 300])
            self.assertEqual(assets[0]["width"], 1080)
            self.assertEqual(assets[0]["height"], 1920)
            self.assertTrue(all(a["qa"]["technical"] == "passed" for a in assets))
            self.assertTrue(all(a["synthetic"] for a in assets))
            candidate = {**analysis["candidates"][0], "title": "Titre corrigé"}
            with patch.object(media, "_call") as runner:
                again = media.render(source, candidate, root / "renders", transcript=transcript, fixture=True)
                runner.assert_not_called()
            self.assertEqual(again["sha256"], assets[0]["sha256"])
            Path(assets[0]["path"]).write_bytes(b"modified")
            with self.assertRaises(ValueError):
                media.render(source, candidate, root / "renders", transcript=transcript, fixture=True)


if __name__ == "__main__":
    unittest.main()
