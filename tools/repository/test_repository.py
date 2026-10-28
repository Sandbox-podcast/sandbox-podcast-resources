import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from archive_local_media import archive_files

spec = importlib.util.spec_from_file_location('repository_policy', Path(__file__).with_name('check_repository.py'))
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class RepositoryPolicyTests(unittest.TestCase):
    def test_archive_preserves_source_bytes_and_records_the_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'exports/video.mp4'
            source.parent.mkdir()
            source.write_bytes(b'local-source')
            destination = root / '.local/archive'
            preview = archive_files(root, ['exports/video.mp4'], destination, apply=False)
            self.assertEqual(len(preview), 1)
            self.assertFalse(destination.exists())
            copied = archive_files(root, ['exports/video.mp4'], destination, apply=True)
            self.assertEqual(copied, preview)
            self.assertEqual(source.read_bytes(), b'local-source')
            self.assertEqual((destination / 'exports/video.mp4').read_bytes(), source.read_bytes())
            self.assertTrue(list(destination.glob('manifest-*.json')))

    def test_archive_refuses_overwriting_another_local_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'source.mp4').write_bytes(b'original')
            destination = root / '.local/archive'
            destination.mkdir(parents=True)
            (destination / 'source.mp4').write_bytes(b'previous-backup')
            with self.assertRaises(ValueError):
                archive_files(root, ['source.mp4'], destination, apply=True)
            self.assertEqual((destination / 'source.mp4').read_bytes(), b'previous-backup')

    def test_archive_refuses_a_versioned_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                archive_files(root, [], root / 'shared-backup', apply=True)

    def test_refuses_media_outputs_and_legacy_paths(self):
        for name in (
            '.local/factory/episodes/e3/pack.json', 'projects/videos/jingle/renders/review.json',
            'projects/videos/intro/public/portrait.svg', 'tools/youtube-growth/output/summary.md',
            'docs/miniature.JPG', 'projects/short.mp4', 'exports/pack.md', 'media/source.wav',
            'kits-relais/post.md', 'projects/relay-kits/e3/production/captions/host.txt',
            'factory.sqlite', 'assets/brand/episode-thumbnail-template-v2.png',
        ):
            with self.subTest(name=name):
                self.assertTrue(policy.local_only(name))

    def test_allows_reusable_sources_and_two_explicit_images(self):
        for name in (
            'README.md', 'config/factory.json', 'assets/brand/logo.png', 'docs/readme/hero.png',
            'assets/brand/youtube/channel-banner-v2.svg', 'projects/videos/jingle/production.html',
            'archive/platform/packages/test.ts', 'docs/factory/validation-2026-10-28.md',
        ):
            with self.subTest(name=name):
                self.assertFalse(policy.local_only(name))

    def test_index_check_refuses_forced_additions(self):
        with patch.object(policy.subprocess, 'check_output', return_value=b'config/factory.json\0forced/SHORT.MP4\0'):
            with patch('builtins.print'):
                self.assertEqual(policy.main(), 1)


if __name__ == '__main__':
    unittest.main()
