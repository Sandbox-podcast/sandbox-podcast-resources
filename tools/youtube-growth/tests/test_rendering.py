from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.rendering import check_render_directory, subtitle_script, validate_render_pack
from youtube_growth.shorts import _render_clip
from youtube_growth.storage import save_json


class RenderValidationTests(unittest.TestCase):
    def setUp(self):
        self.clip = {"id": "d0bc6f817e03def0", "start": 10, "end": 40, "duration": 30, "title": "Un sujet", "selected": True, "layout": "fit"}
        self.pack = {"version": 1, "source_video_id": "GgSiPkADCz4", "source_duration": 100, "candidates": [self.clip]}

    def test_output_path_traversal_is_rejected(self):
        self.clip["id"] = "../../original"
        with self.assertRaises(ValueError):
            validate_render_pack(self.pack)

    def test_inconsistent_duration_and_unknown_crops_are_rejected(self):
        for changes in ({"duration": 31}, {"layout": "automatic-face-crop"}, {"end": float("inf")}):
            value = copy.deepcopy(self.pack)
            value["candidates"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_render_pack(value)

    def test_duplicate_clip_cannot_overwrite_another_export(self):
        self.pack["candidates"].append(copy.deepcopy(self.clip))
        with self.assertRaises(ValueError):
            validate_render_pack(self.pack)

    def test_captions_are_relative_and_cannot_inject_ass_overrides(self):
        value = subtitle_script([{"start": 10, "end": 15, "text": "Bonjour {\\pos(0,0)} tout le monde"}], self.clip)
        self.assertIn("Dialogue: 1,0:00:00.00", value)
        self.assertNotIn("{\\pos", value)
        self.assertIn("PlayResY: 1920", value)

    def test_legacy_renderer_cannot_overwrite_the_source_or_escape_its_directory(self):
        directory = Path(__file__).resolve().parents[1]
        source = directory / "original.mp4"
        for filename in ("original.mp4", "../outside.mp4"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                _render_clip(source, directory, {"file": filename, "srt": "clip.srt"}, [], "unused")

    def test_rerender_cannot_erase_uploaded_ids_or_uncertain_uploads(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temporary:
            directory = Path(temporary)
            for clip in ({"youtube_video_id": "WKrosj0Si5g"}, {"upload_started": True}):
                save_json(directory / "render-manifest.json", {"source_video_id": "GgSiPkADCz4", "source_sha256": "source-hash", "clips": [clip]})
                with self.subTest(clip=clip), self.assertRaises(RuntimeError):
                    check_render_directory(directory, "GgSiPkADCz4", "source-hash")

    def test_another_source_cannot_replace_existing_renders(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temporary:
            directory = Path(temporary)
            save_json(directory / "render-manifest.json", {"source_video_id": "GgSiPkADCz4", "source_sha256": "first-copy", "clips": []})
            with self.assertRaises(ValueError):
                check_render_directory(directory, "GgSiPkADCz4", "another-copy")


if __name__ == "__main__":
    unittest.main()
