"""Portable snapshots must preserve registered thumbnail review inputs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from youtube_growth.factory.backups import backup, restore
from youtube_growth.factory.store import Store


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ThumbnailSnapshotIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.state = self.root / "state"
        directory = self.state / "episodes" / "fixture" / "thumbnails" / "concept"
        directory.mkdir(parents=True)
        self.image = directory / "preview.png"
        self.image.write_bytes(b"reviewed-thumbnail")
        self.brief = directory / "brief.json"
        self.brief.write_text('{"title":"Fixture"}', encoding="utf-8")
        self.receipt = directory / "bundle.json"
        self.receipt.write_text('{}', encoding="utf-8")
        with Store(self.state) as store:
            store.put("thumbnail_bundle", "bundle-fixture", {
                "episode_id": "fixture", "brief_path": str(self.brief), "receipt_path": str(self.receipt),
                "artifacts": [{"path": str(self.image), "kind": "preview_160", "sha256": sha(self.image)}]
            }, episode_id="fixture")
        self.snapshot = self.root / "snapshot.sqlite3"

    def backup(self):
        with Store(self.state) as store:
            return backup(store, self.snapshot, include_media=True)

    def mutate_manifest(self, function):
        manifest = self.snapshot.with_suffix(".manifest.json")
        receipt = json.loads(manifest.read_text(encoding="utf-8"))
        function(receipt)
        manifest.write_text(json.dumps(receipt), encoding="utf-8")

    def test_modified_reviewed_thumbnail_blocks_backup_before_final_output(self):
        self.image.write_bytes(b"modified-after-review")
        with self.assertRaisesRegex(ValueError, "changé"):
            self.backup()
        self.assertFalse(self.snapshot.exists())
        self.assertFalse(self.snapshot.with_suffix(".media").exists())

    def test_removed_thumbnail_or_brief_inventory_entry_blocks_restore(self):
        self.backup()
        manifest = self.snapshot.with_suffix(".manifest.json")
        original = manifest.read_bytes()
        for path in (self.image, self.brief, self.receipt):
            with self.subTest(path=path.name):
                manifest.write_bytes(original)
                self.mutate_manifest(lambda r: r.update(files=[f for f in r["files"] if f["original_path"] != str(path)]))
                target = self.root / "rejected"
                with self.assertRaisesRegex(ValueError, "absent"):
                    restore(self.snapshot, target)
                self.assertFalse(target.exists())

    def test_rehashed_replacement_cannot_override_database_review_hash(self):
        self.backup()
        def replace(receipt):
            row = next(r for r in receipt["files"] if r["original_path"] == str(self.image))
            replacement = self.snapshot.with_suffix(".media") / row["relative_path"]
            replacement.write_bytes(b"different-thumbnail")
            row.update(sha256=sha(replacement), size_bytes=replacement.stat().st_size)
        self.mutate_manifest(replace)
        target = self.root / "rejected"
        with self.assertRaisesRegex(ValueError, "diffère"):
            restore(self.snapshot, target)
        self.assertFalse(target.exists())

    def test_registered_thumbnail_paths_and_hash_survive_restore(self):
        self.backup()
        target = self.root / "restored"
        restore(self.snapshot, target)
        with Store(target) as store:
            bundle = store.get("thumbnail_bundle", "bundle-fixture")
            self.assertTrue(Path(bundle["brief_path"]).is_relative_to(target))
            self.assertTrue(Path(bundle["receipt_path"]).is_file())
            self.assertEqual(sha(Path(bundle["artifacts"][0]["path"])), bundle["artifacts"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
