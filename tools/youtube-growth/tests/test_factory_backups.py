from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory.backups import backup, restore
from youtube_growth.factory.store import Store


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PortableBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.original = self.root / "original"
        self.external = self.original / "owned-sources"
        self.external.mkdir(parents=True)
        self.source = self.external / "master.mp4"
        self.source.write_bytes(b"source-original")
        self.transcript = self.external / "transcript.json"
        self.transcript.write_text(json.dumps({"source_sha256": sha(self.source), "segments": []}), encoding="utf-8")
        self.evidence = self.external / "evidence.json"
        self.evidence.write_text(json.dumps({"source_sha256": sha(self.source), "source": str(self.source)}), encoding="utf-8")
        self.state = self.original / "state"
        self.render_directory = self.state / "episodes" / "fixture" / "renders" / "asset-fixture"
        self.render_directory.mkdir(parents=True)
        self.final = self.render_directory / "video.mp4"
        self.final.write_bytes(b"render-original")
        self.master = self.render_directory / "master-clean.mp4"
        self.master.write_bytes(b"master-original")
        self.subtitles = self.render_directory / "subtitles.srt"
        self.subtitles.write_text("1\n00:00:00,000 --> 00:00:01,000\nFixture de sauvegarde.\n", encoding="utf-8")
        self.ass = self.render_directory / "subtitles.ass"
        self.ass.write_text("[Script Info]\nTitle: Fixture\n", encoding="utf-8")
        self.episode = {"episode_id": "fixture", "source": str(self.source), "source_sha256": sha(self.source),
                        "transcript": str(self.transcript), "evidence": str(self.evidence), "synthetic": True}
        self.asset = {"asset_id": "asset-fixture", "episode_id": "fixture", "path": str(self.final), "sha256": sha(self.final),
                      "master_path": str(self.master), "master_sha256": sha(self.master),
                      "subtitle_path": str(self.subtitles), "subtitle_sha256": sha(self.subtitles),
                      "ass_path": str(self.ass), "ass_sha256": sha(self.ass), "qa_status": "passed"}
        self.render_manifest = self.render_directory / "asset.json"
        self.render_manifest.write_text(json.dumps({**self.asset, "source": str(self.source),
                 "nested": [{"path": str(self.final)}], "prose": "La vidéo vient de "+str(self.source),
                 "url": "https://www.youtube.com/watch?v=abcdefghijk"}), encoding="utf-8")
        with Store(self.state) as store:
            store.put("episode", "fixture", self.episode, episode_id="fixture")
            store.put("asset", "asset-fixture", self.asset, episode_id="fixture")
            store.save_publication({"id": "publication-fixture", "episode_id": "fixture", "platform": "youtube",
                "account_id": "configured-channel", "asset_id": "asset-fixture", "asset_sha256": self.asset["sha256"],
                "status": "simulated", "remote_id": "sim:youtube:fixture", "preview_path": str(self.final)})
            store.enqueue("render", "fixture", {"source": str(self.source), "output": str(self.render_directory)}, key="render-fixture")
        self.snapshot = self.root / "backups" / "snapshot.sqlite3"

    def snapshot_now(self, *, include_media=True):
        with Store(self.state) as store:
            return backup(store, self.snapshot, include_media=include_media)

    def remove_original(self):
        # The target is explicitly confined to this test's temporary workspace.
        self.assertTrue(self.original.resolve().is_relative_to(self.root.resolve()))
        shutil.rmtree(self.original)

    def mutate_receipt(self, update):
        path = self.snapshot.with_suffix(".manifest.json")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        update(receipt)
        path.write_text(json.dumps(receipt), encoding="utf-8")

    def test_portable_snapshot_restores_without_any_original_files(self):
        receipt = self.snapshot_now()
        self.assertTrue(receipt["portable"])
        self.remove_original()
        target = self.root / "restored"
        result = restore(self.snapshot, target)
        self.assertEqual(result["status"], "restored_paused")
        self.assertTrue(result["portable"])
        with Store(target) as store:
            episode, asset = store.get("episode", "fixture"), store.get("asset", "asset-fixture")
            self.assertTrue(store.setting("paused"))
            self.assertEqual(sha(episode["source"]), self.episode["source_sha256"])
            self.assertTrue(Path(episode["source"]).is_relative_to(target / "sources" / "fixture"))
            self.assertTrue(Path(episode["transcript"]).is_file())
            self.assertTrue(Path(episode["evidence"]).is_file())
            self.assertEqual(sha(asset["path"]), self.asset["sha256"])
            self.assertEqual(sha(asset["subtitle_path"]), self.asset["subtitle_sha256"])
            self.assertEqual(asset["asset_id"], "asset-fixture")
            publication = store.publication("publication-fixture")
            self.assertEqual(publication["remote_id"], "sim:youtube:fixture")
            self.assertEqual(publication["preview_path"], asset["path"])
            self.assertEqual(store.jobs()[0]["payload"]["source"], episode["source"])
            manifest = json.loads((Path(asset["path"]).parent / "asset.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["nested"][0]["path"], asset["path"])
            self.assertEqual(manifest["source"], episode["source"])
            self.assertEqual(manifest["url"], "https://www.youtube.com/watch?v=abcdefghijk")
            self.assertEqual(manifest["prose"], "La vidéo vient de "+str(self.source))
            self.assertTrue(result["json_files_remapped"])

    def test_corrupt_database_is_rejected_before_creating_destination(self):
        self.snapshot_now()
        with self.snapshot.open("ab") as stream:
            stream.write(b"corruption")
        target = self.root / "rejected"
        with self.assertRaises(ValueError):
            restore(self.snapshot, target)
        self.assertFalse(target.exists())

    def test_corrupt_media_is_rejected_before_creating_destination(self):
        receipt = self.snapshot_now()
        media = self.snapshot.with_suffix(".media") / receipt["files"][0]["relative_path"]
        media.write_bytes(b"corruption")
        target = self.root / "rejected"
        with self.assertRaises(ValueError):
            restore(self.snapshot, target)
        self.assertFalse(target.exists())

    def test_traversal_and_missing_inventory_entry_are_rejected_before_copy(self):
        original = self.snapshot_now()
        manifest = self.snapshot.with_suffix(".manifest.json")
        for update in (lambda row: row["files"][0].update(relative_path="../outside.mp4"),
                       lambda row: row.update(media_directory="../outside"),
                       lambda row: row.update(database="../different.sqlite3"),
                       lambda row: row.update(files=[])):
            clean = copy.deepcopy({key: value for key, value in original.items() if key not in {"snapshot", "manifest", "media_backup"}})
            manifest.write_text(json.dumps(clean), encoding="utf-8")
            self.mutate_receipt(update)
            target = self.root / "rejected"
            with self.assertRaises(ValueError):
                restore(self.snapshot, target)
            self.assertFalse(target.exists())

    def test_existing_targets_are_never_overwritten(self):
        self.snapshot_now()
        old = self.snapshot.read_bytes()
        with Store(self.state) as store:
            with self.assertRaises(ValueError):
                backup(store, self.snapshot, include_media=True)
        self.assertEqual(self.snapshot.read_bytes(), old)
        target = self.root / "existing"
        target.mkdir()
        with self.assertRaises(ValueError):
            restore(self.snapshot, target)
        self.assertEqual(list(target.iterdir()), [])

    def test_credentials_are_not_collected_and_secret_artifact_blocks_snapshot(self):
        secret = self.original / "youtube-token.json"
        secret.write_text('{"refresh_token":"not-a-real-token"}', encoding="utf-8")
        receipt = self.snapshot_now()
        self.assertNotIn(str(secret), [row["original_path"] for row in receipt["files"]])
        (self.render_directory / "unsafe.json").write_text('{"api_key":"not-a-real-key"}', encoding="utf-8")
        with Store(self.state) as store:
            target = self.root / "secret-rejected.sqlite3"
            with self.assertRaises(ValueError):
                backup(store, target, include_media=True)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_suffix(".media").exists())

    def test_changed_registered_asset_is_rejected_before_writing_snapshot(self):
        self.final.write_bytes(b"changed after review")
        with self.assertRaises(ValueError):
            self.snapshot_now()
        self.assertFalse(self.snapshot.exists())
        self.assertFalse(self.snapshot.with_suffix(".media").exists())

    def test_restore_drops_old_leases_and_keeps_sends_unknown(self):
        with Store(self.state) as store:
            row = store.publication("publication-fixture")
            row["status"] = "sending"
            store.save_publication(row)
            store.db.execute("UPDATE jobs SET status='running',owner='old-worker',lease_until='2099-01-01T00:00:00Z'")
            dispatch = store.enqueue("dispatch", "fixture", {"publication_id": "publication-fixture"}, key="dispatch-fixture")
            store.db.execute("UPDATE jobs SET status='running',owner='old-worker',lease_until='2099-01-01T00:00:00Z' WHERE id=?", (dispatch,))
        self.snapshot_now()
        target = self.root / "restored"
        restore(self.snapshot, target)
        with Store(target) as store:
            self.assertTrue(store.setting("paused"))
            self.assertEqual(store.publication("publication-fixture")["status"], "unknown")
            states = {job["kind"]: job for job in store.jobs()}
            self.assertEqual(states["dispatch"]["status"], "unknown")
            self.assertEqual(states["render"]["status"], "queued")
            self.assertIsNone(states["render"]["owner"])
            self.assertIsNone(states["render"]["lease_until"])

    def test_database_only_snapshot_is_explicitly_not_portable(self):
        self.snapshot_now(include_media=False)
        self.remove_original()
        result = restore(self.snapshot, self.root / "database-only")
        self.assertFalse(result["portable"])
        self.assertEqual(result["media_files"], 0)
        self.assertIn("database_only_media_not_restored", result["limitations"])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg et ffprobe requis pour le cache média réel.")
class PortableMediaCacheTests(unittest.TestCase):
    def test_real_render_cache_is_reused_after_original_workspace_disappears(self):
        from youtube_growth.factory import media
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "original"
            original.mkdir()
            source = original / "source.mp4"
            subprocess.run([shutil.which("ffmpeg"), "-nostdin", "-v", "error", "-n", "-f", "lavfi", "-i",
                            "color=c=0x2288bb:size=128x72:rate=12:duration=2", "-f", "lavfi", "-i",
                            "sine=frequency=440:sample_rate=48000:duration=2", "-c:v", "libx264", "-preset", "ultrafast",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)],
                           check=True, capture_output=True)
            state = original / "state"
            candidate = {"segment_id": "segment-fixture", "start_seconds": 0, "end_seconds": 2, "title": "Fixture cache"}
            asset = media.render(source, candidate, state / "episodes" / "fixture" / "renders", format="horizontal", fixture=True)
            asset["episode_id"] = "fixture"
            with Store(state) as store:
                store.put("episode", "fixture", {"episode_id": "fixture", "source": str(source), "source_sha256": sha(source)})
                store.put("asset", asset["asset_id"], asset, episode_id="fixture")
                snapshot = root / "snapshot.sqlite3"
                backup(store, snapshot, include_media=True)
            self.assertTrue(original.resolve().is_relative_to(root.resolve()))
            shutil.rmtree(original)
            target = root / "restored"
            restore(snapshot, target)
            with Store(target) as store:
                episode = store.get("episode", "fixture")
                restored = store.get("asset", asset["asset_id"])
                before = Path(restored["path"]).stat().st_mtime_ns
                # No mocks: real ffprobe validates the restored source; success
                # and unchanged mtime prove the finished media was not re-encoded.
                reused = media.render(Path(episode["source"]), candidate, target / "episodes" / "fixture" / "renders",
                                      format="horizontal", fixture=True)
                self.assertEqual(reused["asset_id"], restored["asset_id"])
                self.assertEqual(reused["sha256"], restored["sha256"])
                self.assertEqual(Path(reused["path"]).stat().st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
