from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from youtube_growth.social import build_packs, generate
from youtube_growth.shorts import _sha256
from youtube_growth.storage import save_json


def plan():
    return {"version": 1, "video_id": "AbCdEfGhI12", "source_duration": 120,
            "clips": [{"id": "usage-restaurant", "variants": [
                {"platform": "youtube", "start": 10, "end": 55, "title": "La question complète",
                 "caption": "Découvrir le raisonnement complet.", "layout": "fit"},
                {"platform": "tiktok", "start": 18, "end": 48, "title": "Le résultat concret",
                 "caption": "Comment ferais-tu ?", "layout": "fit"},
                {"platform": "instagram", "start": 15, "end": 50, "title": "Le cas métier à retenir",
                 "caption": "Un exemple à conserver.", "layout": "fit"}]}]}


class SocialTests(unittest.TestCase):
    def test_distinct_network_ranges_titles_and_captions(self):
        rows = build_packs(plan())
        self.assertEqual([r["pack"]["candidates"][0]["duration"] for r in rows], [45, 30, 35])
        self.assertEqual(len({r["pack"]["candidates"][0]["id"] for r in rows}), 3)
        self.assertEqual(len({r["caption"] for r in rows}), 3)

    def test_thirty_clips_do_not_inherit_the_native_pack_ten_candidate_limit(self):
        data = plan()
        data["clips"] = [dict(deepcopy(data["clips"][0]), id=f"clip-{i}") for i in range(30)]
        self.assertEqual(len(build_packs(data)), 90)

    def test_rejects_unknown_network_duplicate_paths_and_bad_ranges(self):
        for field, value in (("platform", "facebook"), ("platform", []), ("start", True),
                             ("end", 500), ("caption", ""), ("layout", "unknown")):
            data = plan()
            data["clips"][0]["variants"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                build_packs(data)
        data = plan()
        data["clips"][0]["id"] = "../outside"
        with self.assertRaises(ValueError):
            build_packs(data)
        data = plan()
        data["clips"].append(deepcopy(data["clips"][0]))
        with self.assertRaises(ValueError):
            build_packs(data)
        data = plan()
        data["clips"][0]["variants"].append(deepcopy(data["clips"][0]["variants"][0]))
        with self.assertRaises(ValueError):
            build_packs(data)

    def test_simulation_does_not_create_outputs_or_call_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, transcript = root / "source.mp4", root / "transcript.txt"
            source.write_bytes(b"source")
            transcript.write_text("transcript")
            with patch("youtube_growth.social.render_pack") as render:
                result = generate(plan(), source, transcript, root / "output")
            self.assertTrue(result["dry_run"])
            self.assertEqual(result["publication"], "not_uploaded")
            self.assertFalse((root / "output").exists())
            render.assert_not_called()

    def test_resume_reuses_identical_media_and_refuses_changed_plan_or_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, transcript = root / "source.mp4", root / "transcript.txt"
            source.write_bytes(b"source")
            transcript.write_text("transcript")
            output = root / "output"

            def fake_render(src, txt, pack_path, target):
                candidate = json.loads(pack_path.read_text(encoding="utf-8"))["candidates"][0]
                media = target / (candidate["id"] + ".mp4")
                media.write_bytes(candidate["title"].encode())
                row = {**candidate, "file": str(media), "technical_status": "decoded",
                       "render_sha256": _sha256(media)}
                result = {"source_sha256": _sha256(src), "clips": [row]}
                save_json(target / "render-manifest.json", result)
                return result

            with patch("youtube_growth.social.render_pack", side_effect=fake_render) as render:
                generate(plan(), source, transcript, output, execute=True)
                self.assertEqual(render.call_count, 3)
                generate(plan(), source, transcript, output, execute=True)
                self.assertEqual(render.call_count, 3)
                changed = plan()
                changed["clips"][0]["variants"][0]["end"] = 56
                with self.assertRaises(ValueError):
                    generate(changed, source, transcript, output, execute=True)
                row = json.loads((output / "social-manifest.json").read_text(encoding="utf-8"))["results"][0]
                Path(row["file"]).write_bytes(b"changed")
                with self.assertRaises(ValueError):
                    generate(plan(), source, transcript, output, execute=True)
                self.assertEqual(render.call_count, 3)

    def test_source_inside_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            with self.assertRaises(ValueError):
                generate(plan(), source, source, root, execute=True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg et ffprobe requis")
    def test_real_two_network_export_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, transcript = root / "source.mp4", root / "transcript.txt"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=blue:size=1280x720:rate=3:duration=9", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=9", "-c:v", "libx264", "-preset", "ultrafast",
                            "-c:a", "aac", "-shortest", str(source)], check=True, capture_output=True)
            transcript.write_text("Video ID: AbCdEfGhI12\n[00:00] Une question.\n[00:03] Une explication.\n[00:06] La conclusion.\n", encoding="utf-8")
            data = plan()
            data["source_duration"] = 9
            data["clips"][0]["variants"] = data["clips"][0]["variants"][:2]
            for variant, start, end in zip(data["clips"][0]["variants"], [0, 2], [5, 8], strict=True):
                variant.update(start=start, end=end)
            output = root / "outputs"
            result = generate(data, source, transcript, output, execute=True)
            self.assertEqual(result["variants"], 2)
            rows = json.loads((output / "social-manifest.json").read_text(encoding="utf-8"))["results"]
            self.assertEqual({row["platform"] for row in rows}, {"youtube", "tiktok"})
            mtimes = [Path(row["file"]).stat().st_mtime_ns for row in rows]
            with patch("youtube_growth.social.render_pack", side_effect=AssertionError("Rendu répété")):
                generate(data, source, transcript, output, execute=True)
            self.assertEqual(mtimes, [Path(row["file"]).stat().st_mtime_ns for row in rows])


if __name__ == "__main__":
    unittest.main()
