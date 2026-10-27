import copy
import importlib.util
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

import pipeline


class SourcePipelineTests(unittest.TestCase):
    def setUp(self):
        self.manifest = pipeline.read_json(pipeline.HERE / 'manifest.json')

    def test_thirty_source_compositions_have_one_video_and_valid_timings(self):
        clips = pipeline.validate_manifest(self.manifest)
        self.assertEqual(len(clips), 30)
        self.assertEqual({clip['id'] for clip in clips}, {f'E02-{index:03d}' for index in range(1, 31)})
        for clip in clips:
            html = (pipeline.HERE / 'projects' / pipeline.project_slug(clip) / 'index.html').read_text(encoding='utf-8')
            self.assertIn("window.__timelines['main']", html)
            self.assertNotIn('<div class="context">', html)
            self.assertNotIn('C:/', html)

    def test_rejects_invalid_ranges_and_duplicate_ids(self):
        for key, value in [('start', -1), ('duration', float('nan')), ('end', 0)]:
            manifest = copy.deepcopy(self.manifest)
            manifest['clips'][0][key] = value
            with self.assertRaises(ValueError):
                pipeline.validate_manifest(manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest['clips'][1]['id'] = manifest['clips'][0]['id']
        with self.assertRaises(ValueError):
            pipeline.validate_manifest(manifest)

    def test_versioned_html_matches_source_inventory_after_formatting(self):
        records = pipeline.read_json(pipeline.HERE / 'source-provenance.json')['projects']
        self.assertEqual(len(records), 30)
        for record in records:
            path = pipeline.child(pipeline.HERE, 'projects/' + record['project'] + '/index.html')
            self.assertEqual(pipeline.digest(path), record['versioned_sha256'])

    def test_rejects_paths_outside_workspace_and_source_destinations(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            with self.assertRaises(ValueError):
                pipeline.child(base, '../outside.mp4')
            with self.assertRaises(ValueError):
                pipeline.child(base, base.parent / 'outside.mp4')
            with self.assertRaises(ValueError):
                pipeline.new_directory(base)
        with self.assertRaises(ValueError):
            pipeline.new_directory(pipeline.HERE / 'generated-media')
        with self.assertRaises(ValueError):
            pipeline.existing_workspace(pipeline.HERE)

    def test_write_commands_default_to_dry_run_without_network_or_processes(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder) / 'not-created'
            with patch.object(pipeline, 'run', side_effect=AssertionError('Aucun processus attendu')):
                result = pipeline.main(['prepare', '--workspace', str(workspace), '--episode', 'episode.mp4', '--gsap', 'gsap.min.js', '--font', 'archivo.woff2', '--logo', 'logo.png'])
            self.assertTrue(result['dry_run'])
            self.assertFalse(workspace.exists())

    def test_unknown_clip_does_not_select_or_render_anything(self):
        with self.assertRaises(ValueError):
            pipeline.selected_clips(self.manifest, ['E02-999'])

    def test_import_has_no_render_or_file_side_effect(self):
        with patch('subprocess.run', side_effect=AssertionError('Import sans exécution externe')):
            spec = importlib.util.spec_from_file_location('pipeline_import_test', pipeline.HERE / 'pipeline.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.REVISION, 'camera-unique-v2')

    def test_instagram_ranges_stay_in_validated_master_and_under_ninety_seconds(self):
        for clip_id, ranges in self.manifest['instagram_ranges'].items():
            clip = next(clip for clip in self.manifest['clips'] if clip['id'] == clip_id)
            self.assertLess(sum(end - start for start, end in ranges), 90)
            for start, end in ranges:
                self.assertGreaterEqual(start, 0)
                self.assertGreater(end, start)
                self.assertLessEqual(end, math.ceil(clip['duration'] * 30) / 30 + .001)

    def test_audio_correlation_accepts_identical_signal_without_shift(self):
        source = np.random.default_rng(42).normal(size=32000)
        result = pipeline.audio_correlation(source, source.copy())
        self.assertEqual(result['status'], 'audio_matches_source')
        self.assertTrue(all(check['correlation'] > .999 and check['lag_ms'] == 0 for check in result['checks']))
        self.assertFalse(result['full_listening'])

    def test_audio_correlation_requires_review_for_shift_noise_silence_or_truncation(self):
        source = np.random.default_rng(42).normal(size=32000)
        shifted = np.concatenate([np.zeros(400), source[:-400]])
        for output in [shifted, np.random.default_rng(43).normal(size=32000), np.zeros(32000), source[:-1600]]:
            with self.subTest(samples=len(output)):
                self.assertEqual(pipeline.audio_correlation(source, output)['status'], 'review_required')
        with self.assertRaises(ValueError):
            pipeline.audio_correlation(source[:100], source[:100])

    def prepare_install_fixture(self, base):
        workspace = base / 'workspace'
        (workspace / 'shorts').mkdir(parents=True)
        pipeline.write_json(workspace / 'manifest.json', self.manifest)
        shutil.copytree(pipeline.HERE / 'projects', workspace / 'projects')
        provenance = []
        video, audio, visual = [], [], []
        for clip in self.manifest['clips']:
            path = workspace / 'shorts' / (pipeline.project_slug(clip) + '.mp4')
            path.write_bytes(('fixture-' + clip['id']).encode())
            checksum = pipeline.digest(path)
            project = workspace / 'projects' / pipeline.project_slug(clip)
            composition = pipeline.Composition((project / 'index.html').read_text(encoding='utf-8'))
            source = pipeline.child(project, composition.videos[0]['src'])
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(('source-' + clip['id']).encode())
            source_checksum = pipeline.digest(source)
            provenance.append({'id': clip['id'], 'mezzanine_sha256': source_checksum})
            video.append({'id': clip['id'], 'sha256': checksum, 'status': 'rendered_verified'})
            audio.append({'id': clip['id'], 'sha256': checksum, 'source_sha256': source_checksum, 'status': 'audio_matches_source'})
            visual.append({'id': clip['id'], 'sha256': checksum, 'status': 'reviewed', 'reviewed_by': 'fixture reviewer'})
        for name, rows in [('render-status.json', video), ('audio-qa.json', audio), ('visual-review.json', visual)]:
            pipeline.write_json(workspace / name, rows)
        pipeline.write_json(workspace / 'provenance.json', {'clips': provenance})
        return workspace

    def test_install_rejects_changed_source_missing_audio_binding_or_changed_provenance(self):
        for mode in ['changed_source', 'missing_audio_binding', 'changed_provenance']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                workspace = self.prepare_install_fixture(base)
                clip = self.manifest['clips'][0]
                project = workspace / 'projects' / pipeline.project_slug(clip)
                composition = pipeline.Composition((project / 'index.html').read_text(encoding='utf-8'))
                if mode == 'changed_source':
                    pipeline.child(project, composition.videos[0]['src']).write_bytes(b'replaced source')
                elif mode == 'missing_audio_binding':
                    rows = pipeline.read_json(workspace / 'audio-qa.json')
                    del rows[0]['source_sha256']
                    pipeline.write_json(workspace / 'audio-qa.json', rows)
                else:
                    provenance = pipeline.read_json(workspace / 'provenance.json')
                    provenance['clips'][0]['mezzanine_sha256'] = 'different source'
                    pipeline.write_json(workspace / 'provenance.json', provenance)
                target = base / 'bundle'
                with self.assertRaises(ValueError):
                    pipeline.install(self.manifest, workspace, target)
                self.assertFalse(target.exists())

    def test_render_validates_actual_workspace_compositions_before_processes(self):
        for mode in ['second_video', 'changed_duration']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                workspace = self.prepare_install_fixture(Path(folder))
                project = workspace / 'projects' / pipeline.project_slug(self.manifest['clips'][0])
                html = project / 'index.html'
                content = html.read_text(encoding='utf-8')
                if mode == 'second_video':
                    content += '<video src="assets/second.mp4"></video>'
                else:
                    content = content.replace('data-duration="33.8"', 'data-duration="99"', 1)
                html.write_text(content, encoding='utf-8')
                with patch.object(pipeline, 'run', side_effect=AssertionError('Aucun processus attendu')):
                    with self.assertRaises(ValueError):
                        pipeline.render(self.manifest, workspace, sys.executable, ['E02-001'])

    def test_render_rejects_output_or_log_symlinks_outside_workspace(self):
        for name in ['shorts', 'render-logs']:
            with self.subTest(directory=name), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                workspace = self.prepare_install_fixture(base)
                outside = base / 'outside'
                outside.mkdir()
                target = workspace / name
                if target.exists():
                    shutil.rmtree(target)
                if sys.platform == 'win32':
                    import _winapi
                    _winapi.CreateJunction(str(outside), str(target))
                else:
                    target.symlink_to(outside, target_is_directory=True)
                with patch.object(pipeline, 'run', side_effect=AssertionError('Aucun processus attendu')):
                    with self.assertRaises(ValueError):
                        pipeline.render(self.manifest, workspace, sys.executable, ['E02-001'])
                self.assertEqual(list(outside.iterdir()), [])

    def test_install_copies_checked_bytes_to_fresh_bundle_without_touching_publication_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            workspace = self.prepare_install_fixture(base)
            queue = base / 'publication-queue.json'
            queue.write_text('DO NOT MODIFY', encoding='utf-8')
            target = base / 'bundle'
            result = pipeline.install(self.manifest, workspace, target)
            self.assertEqual(result['publication'], 'not_uploaded')
            self.assertEqual(len(list(target.glob('*.mp4'))), 30)
            self.assertEqual(queue.read_text(encoding='utf-8'), 'DO NOT MODIFY')
            for source in (workspace / 'shorts').glob('*.mp4'):
                self.assertEqual(pipeline.digest(source), pipeline.digest(target / source.name))
            with self.assertRaises(ValueError):
                pipeline.install(self.manifest, workspace, target)

    def test_install_rejects_stale_checksums_missing_review_and_missing_files_before_writing(self):
        for mode in ['modified_media', 'missing_review', 'missing_file', 'empty_reviewer']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                workspace = self.prepare_install_fixture(base)
                first = self.manifest['clips'][0]
                media = workspace / 'shorts' / (pipeline.project_slug(first) + '.mp4')
                if mode == 'modified_media':
                    media.write_bytes(b'changed since review')
                elif mode == 'missing_file':
                    media.unlink()
                else:
                    reviews = pipeline.read_json(workspace / 'visual-review.json')
                    if mode == 'missing_review':
                        reviews.pop()
                    else:
                        reviews[0]['reviewed_by'] = ''
                    pipeline.write_json(workspace / 'visual-review.json', reviews)
                target = base / 'bundle'
                with self.assertRaises((ValueError, FileNotFoundError)):
                    pipeline.install(self.manifest, workspace, target)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
