"""Stage reuse must save computation without bypassing content integrity."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from youtube_growth.factory import media


class MediaEfficiencyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"owned-source")
        self.output = self.root / "analysis"
        self.evidence = self.root / "evidence.json"
        self.info = {"duration_seconds": 100,
                     "streams": [{"codec_type": "video", "codec_name": "h264", "width": 640, "height": 360},
                                 {"codec_type": "audio", "codec_name": "aac"}]}
        self.technical = {"decode": "passed", "black_intervals_seconds": [], "silence_events": [], "max_volume_db": -3.0}
        self.candidate = {"start_seconds": 0, "end_seconds": 12, "title": "Premier titre",
                          "source_sha256": media.fingerprint(self.source)}

    def analyze(self):
        with patch.object(media, "probe", return_value=self.info), \
             patch.object(media, "_scan", return_value=self.technical), \
             patch.object(media, "_frames", return_value=[]):
            return media.analyze(self.source, None, self.output,
                                 evidence=self.evidence if self.evidence.exists() else None)

    def render_probe(self, path):
        if path.name == "video.mp4":
            return {"duration_seconds": 12,
                    "streams": [{"codec_type": "video", "codec_name": "h264", "duration": "12", "width": 1080, "height": 1920},
                                {"codec_type": "audio", "codec_name": "aac", "duration": "12"}]}
        return self.info

    @staticmethod
    def encode(arguments):
        Path(arguments[-1]).write_bytes(b"encoded-stage")
        return ""

    def render(self, candidate=None):
        with patch.object(media, "_require_media_tools", return_value=("ffmpeg", "ffprobe")), \
             patch.object(media, "probe", side_effect=self.render_probe), \
             patch.object(media, "_call", side_effect=self.encode), \
             patch.object(media, "_scan", return_value=self.technical), \
             patch.object(media, "_frames", return_value=[]):
            return media.render(self.source, candidate or self.candidate, self.root / "renders", fixture=True)

    def test_unchanged_analysis_does_not_probe_decode_or_extract_again(self):
        first = self.analyze()
        with patch.object(media, "probe") as probe, patch.object(media, "_scan") as scan, \
             patch.object(media, "_frames") as frames:
            second = media.analyze(self.source, None, self.output)
        probe.assert_not_called()
        scan.assert_not_called()
        frames.assert_not_called()
        self.assertEqual(first["cache_key"], second["cache_key"])
        self.assertEqual(second["execution_cache"]["analysis"], "hit")

    def test_editorial_revision_reuses_source_probe_and_technical_scan(self):
        self.analyze()
        self.evidence.write_text(json.dumps({"version": 1, "source_sha256": media.fingerprint(self.source),
                                             "provenance": {"kind": "human_review", "reviewer": "test-reviewer"}}), encoding="utf-8")
        with patch.object(media, "probe") as probe, patch.object(media, "_scan") as scan, \
             patch.object(media, "_frames", return_value=[]):
            revised = media.analyze(self.source, None, self.output, evidence=self.evidence)
        probe.assert_not_called()
        scan.assert_not_called()
        self.assertEqual(revised["provenance"]["reviewer"], "test-reviewer")
        self.assertEqual(revised["execution_cache"], {"analysis": "miss", "source_probe": "hit", "technical_scan": "hit"})

    def test_source_change_with_same_size_and_mtime_is_not_a_cache_hit(self):
        first = self.analyze()
        before = self.source.stat()
        self.source.write_bytes(b"other-source")
        os.utime(self.source, ns=(before.st_atime_ns, before.st_mtime_ns))
        with patch.object(media, "probe", return_value=self.info) as probe, \
             patch.object(media, "_scan", return_value=self.technical) as scan, \
             patch.object(media, "_frames", return_value=[]):
            second = media.analyze(self.source, None, self.output)
        probe.assert_called_once()
        scan.assert_called_once()
        self.assertNotEqual(first["cache_key"], second["cache_key"])

    def test_analysis_mutation_does_not_commit_source_stage_receipts(self):
        def mutate_source(path):
            path.write_bytes(b"other-source")
            return self.technical
        with patch.object(media, "probe", return_value=self.info), \
             patch.object(media, "_scan", side_effect=mutate_source), \
             patch.object(media, "_frames", return_value=[]), self.assertRaisesRegex(ValueError, "changé"):
            media.analyze(self.source, None, self.output)
        self.assertEqual(list(self.output.glob("*.json")), [])

    def test_tampered_probe_receipt_cannot_supply_a_duration(self):
        self.analyze()
        probe_path = next(self.output.glob("probe-*.json"))
        value = json.loads(probe_path.read_text(encoding="utf-8"))
        value["payload"]["duration_seconds"] = 1000
        probe_path.write_text(json.dumps(value), encoding="utf-8")
        self.evidence.write_text(json.dumps({"version": 1, "source_sha256": media.fingerprint(self.source)}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cache média"):
            self.analyze()

    def test_title_revision_reuses_source_probe_and_checks_all_finished_outputs(self):
        first = self.render()
        with patch.object(media, "probe") as probe, patch.object(media, "_call") as encoder, \
             patch.object(media, "_scan") as scan:
            second = media.render(self.source, {**self.candidate, "title": "Titre corrigé"}, self.root / "renders", fixture=True)
        probe.assert_not_called()
        encoder.assert_not_called()
        scan.assert_not_called()
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(second["execution_cache"]["render"], "hit")
        Path(first["master_path"]).write_bytes(b"tampered-master")
        with self.assertRaisesRegex(ValueError, "export terminé"):
            media.render(self.source, self.candidate, self.root / "renders", fixture=True)

    def test_new_cuts_reuse_source_probe_but_produce_a_distinct_asset(self):
        first = self.render()
        candidate = {**self.candidate, "start_seconds": 12, "end_seconds": 24}
        with patch.object(media, "_require_media_tools", return_value=("ffmpeg", "ffprobe")), \
             patch.object(media, "probe", side_effect=self.render_probe) as probe, \
             patch.object(media, "_call", side_effect=self.encode) as encoder, \
             patch.object(media, "_scan", return_value=self.technical), \
             patch.object(media, "_frames", return_value=[]):
            second = media.render(self.source, candidate, self.root / "renders", fixture=True)
        self.assertNotEqual(first["asset_id"], second["asset_id"])
        self.assertEqual(second["cuts"][0]["source_start_seconds"], 12)
        encoder.assert_called_once()
        self.assertEqual([call.args[0].name for call in probe.call_args_list], ["video.mp4"])
        self.assertEqual(second["execution_cache"]["source_probe"], "hit")

    def test_frame_failure_preserves_successful_technical_qa_for_restart(self):
        with patch.object(media, "_require_media_tools", return_value=("ffmpeg", "ffprobe")), \
             patch.object(media, "probe", side_effect=self.render_probe), \
             patch.object(media, "_call", side_effect=self.encode), \
             patch.object(media, "_scan", return_value=self.technical), \
             patch.object(media, "_frames", side_effect=RuntimeError("frame_interrupted")), \
             self.assertRaisesRegex(RuntimeError, "frame_interrupted"):
            media.render(self.source, self.candidate, self.root / "renders", fixture=True)
        with patch.object(media, "_require_media_tools", return_value=("ffmpeg", "ffprobe")), \
             patch.object(media, "probe", side_effect=self.render_probe) as probe, \
             patch.object(media, "_call") as encoder, patch.object(media, "_scan") as scan, \
             patch.object(media, "_frames", return_value=[]):
            restarted = media.render(self.source, self.candidate, self.root / "renders", fixture=True)
        encoder.assert_not_called()
        scan.assert_not_called()
        self.assertEqual([call.args[0] for call in probe.call_args_list], [self.source])
        self.assertEqual(restarted["execution_cache"]["technical_qa"], "hit")
        self.assertEqual(restarted["qa"]["visual"], "pending_human_review")

    def test_mutation_during_qa_does_not_commit_technical_receipt(self):
        def mutate_output(path):
            path.write_bytes(b"tampered-output")
            return self.technical
        with patch.object(media, "_require_media_tools", return_value=("ffmpeg", "ffprobe")), \
             patch.object(media, "probe", side_effect=self.render_probe), \
             patch.object(media, "_call", side_effect=self.encode), \
             patch.object(media, "_scan", side_effect=mutate_output), \
             self.assertRaisesRegex(ValueError, "changé"):
            media.render(self.source, self.candidate, self.root / "renders", fixture=True)
        self.assertEqual(list((self.root / "renders").glob("*/technical-*.json")), [])


if __name__ == "__main__":
    unittest.main()
