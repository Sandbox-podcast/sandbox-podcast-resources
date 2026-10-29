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
from youtube_growth.factory.store import Store
from youtube_growth.factory.contracts import load_config
from youtube_growth.factory import runtime


class LocalPackReplacementTests(unittest.TestCase):
    def test_new_local_render_replaces_archived_pack_but_preserves_remote_terminal_intent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source.mp4';source.write_bytes(b'owned-source')
            old=root/'old.mp4';new=root/'new.mp4';old.write_bytes(b'old');new.write_bytes(b'new')
            episode={'episode_id':'local-e','source':str(source),'local_autonomy':True,'revision':'r'}
            candidate={'segment_id':'c','episode_id':'local-e','episode_revision':'r','decision':'retained',
                       'local_only':True,'title':'Titre','platforms':['youtube']}
            def rendered(path):return {'asset_id':path.stem,'path':str(path),'sha256':media.fingerprint(path),'format':'horizontal','qa_status':'needs_review'}
            with Store(root/'state') as store:
                store.put('episode','local-e',episode,episode_id='local-e');store.put('candidate','c',candidate,episode_id='local-e')
                with patch.object(media,'render',return_value=rendered(old)):
                    runtime.render_candidate(store,load_config(),'local-e','c','horizontal')
                pack=store.publications('local-e')[0];pack.update(local_only=True,status='archived');store.save_publication(pack)
                with patch.object(media,'render',return_value=rendered(new)):
                    runtime.render_candidate(store,load_config(),'local-e','c','horizontal')
                current=store.publication(pack['id'])
                self.assertEqual(current['asset_sha256'],media.fingerprint(new))
                self.assertNotEqual(current['status'],'archived')
                current.update(status='published',remote_id='remote-keep');store.save_publication(current)
                with patch.object(media,'render',return_value=rendered(old)):
                    runtime.render_candidate(store,load_config(),'local-e','c','horizontal')
                self.assertEqual(store.publication(pack['id'])['remote_id'],'remote-keep')
                self.assertEqual(store.publication(pack['id'])['asset_sha256'],media.fingerprint(new))


@unittest.skipUnless(os.environ.get('FACTORY_MEDIA_INTEGRATION')=='1','Recette média explicite requise')
class LocalCaptionBandMediaTests(unittest.TestCase):
    def test_real_export_preserves_bottom_marker_and_groups_fleeting_final_word(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source.mp4';transcript=root/'transcript.json'
            ffmpeg,_=media._require_media_tools()
            media._call([ffmpeg,'-nostdin','-v','error','-n','-f','lavfi','-i','color=c=0x1450a0:s=640x360:r=30:d=4',
                '-f','lavfi','-i','sine=frequency=440:duration=4','-vf','drawbox=x=0:y=330:w=iw:h=30:color=red:t=fill',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(source)])
            transcript.write_text(json.dumps({'source_sha256':media.fingerprint(source),'segments':[
                {'start':0,'end':1,'text':'Une idée qui est hyper'},{'start':1,'end':1.28,'text':'utile.'}]}),encoding='utf-8')
            result=media.render(source,{'start_seconds':0,'end_seconds':4,'render_profile':'local_caption_band_v1'},root/'renders',format='horizontal',transcript=transcript,fixture=True)
            self.assertEqual(result['parameters']['subtitle_grouping_version'],2)
            self.assertEqual(Path(result['subtitle_path']).read_text(encoding='utf-8-sig').count('-->'),1)
            self.assertIn('utile.',Path(result['ass_path']).read_text(encoding='utf-8-sig'))
            frame=root/'final.png'
            media._call([ffmpeg,'-nostdin','-v','error','-n','-ss','0.8','-i',result['path'],'-frames:v','1',str(frame)])
            with Image.open(frame).convert('RGB') as image:
                red=[y for y in range(image.height) if (lambda c:c[0]>150 and c[1]<100 and c[2]<100)(image.getpixel((image.width//2,y)))]
                self.assertGreater(len(red),5)
                self.assertLess(max(red),image.height-result['parameters']['caption_band_pixels'])
                self.assertLess(max(abs(a-b) for a,b in zip(image.getpixel((5,image.height-5)),(7,19,34))),12)


class ProcessLockTests(unittest.TestCase):
    def test_process_death_releases_lock_without_unlinking_the_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "from pathlib import Path; import sys,time; from youtube_growth.factory.local_lock import local_lock; " \
                     "lock=local_lock(Path(sys.argv[1])); lock.__enter__(); print('locked',flush=True); time.sleep(60)"
            environment = {**os.environ, "PYTHONPATH": os.pathsep.join(str(Path(p).resolve()) for p in sys.path if p)}
            # Windows venv python.exe is a launcher: terminate the actual process
            # holding the lock, rather than leaving its interpreter child alive.
            interpreter = sys._base_executable if os.name == "nt" else sys.executable
            child = subprocess.Popen([interpreter, "-u", "-c", script, str(root)], stdout=subprocess.PIPE,
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
    def test_local_caption_band_keeps_static_text_and_legacy_animation(self):
        rows = [{'start': 1, 'end': 2, 'text': 'Une phrase entière.'}]
        cuts = [{'source_start_seconds': 0, 'source_end_seconds': 3,
                 'output_start_seconds': 0, 'output_end_seconds': 3}]
        legacy = media._ass_subtitles(rows, cuts, (1280, 720), False)
        local = media._ass_subtitles(rows, cuts, (1280, 720), False, group_short=True, caption_band=128)
        self.assertIn(r'\fad(60,50)', legacy)
        self.assertNotIn(r'\fad(', local)
        self.assertIn('Une phrase entière.', local)
        self.assertIn('0:00:01.00,0:00:02.00', local)

    def test_short_caption_keeps_final_word_visible_with_previous_phrase(self):
        rows=[{'start':1,'end':2,'text':"Une idée qui est hyper"},{'start':2,'end':2.28,'text':'utile.'}]
        merged=media._caption_units(rows)
        self.assertEqual(merged,[{'start':1,'end':2.28,'text':"Une idée qui est hyper utile."}])
        cuts=[{'source_start_seconds':0,'source_end_seconds':3,'output_start_seconds':0,'output_end_seconds':3}]
        srt=media._subtitles(rows,cuts,group_short=True)
        self.assertEqual(srt.count('-->'),1)
        self.assertIn('utile.',srt)
        ass=media._ass_subtitles(rows,cuts,(1280,720),False,group_short=True,caption_band=128)
        self.assertEqual(ass.count('Dialogue:'),1)
        self.assertIn('utile.',ass)
        self.assertEqual(len(media._caption_units([rows[0],{'start':4,'end':4.28,'text':'Autre sujet.'}])),2)
        professional=media._caption_units([{'start':182.99,'end':185.04,'text':'à une application'},
                                         {'start':185.78,'end':186.10,'text':'professionnelle.'}])
        self.assertEqual(professional,[{'start':182.99,'end':186.10,'text':'à une application professionnelle.'}])
        split=[{**cuts[0],'source_end_seconds':2,'output_end_seconds':2},
               {'source_start_seconds':2,'source_end_seconds':3,'output_start_seconds':2,'output_end_seconds':3}]
        self.assertEqual(media._subtitles(rows,split,group_short=True).count('-->'),2)

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
