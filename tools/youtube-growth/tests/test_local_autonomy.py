"""State-machine and failure tests; inference/media doubles are explicit."""
from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
from types import SimpleNamespace
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from youtube_growth.factory import autonomy, local_alignment, local_audio, local_faces, local_models, local_quality, local_revisions, local_review, runtime, scheduler
from youtube_growth.factory.local_transcript import proofread, same_spoken_words
from youtube_growth.factory.contracts import digest, load_config
from youtube_growth.factory.media import fingerprint
from youtube_growth.factory.store import Store

NOW = "2026-10-29T08:00:00+01:00"


class ModelDouble:
    reject_title = None
    empty = False
    unsupported_evidence = False
    overlapping_alternative = False
    unsupported_title = None
    incomplete_edges_title = None
    reject_packaging_language = False
    reject_packaging_hypothesis = False

    def __init__(self, config, directory):
        self.options = config["autonomy"]
        self.directory = directory

    def complete(self, role, prompt, data, schema, *, images=None, reviewer=False, validator=None):
        if role == "transcript_orthography_tokens":
            result = {"edits": []}
        elif role == "selection":
            result = {"summary": "Démonstration synthétique de contrôles locaux.", "candidates": []}
            if not self.empty:
                choices = [(0, 1, "Contrôler les sources"), (2, 3, "Préserver le contexte")]
                if self.overlapping_alternative:
                    choices.insert(1, (0, 2, "Variante déjà couverte"))
                for first, last, name in choices:
                    result["candidates"].append({"start_index": first, "end_index": last, "quote_index": first,
                        "title": name, "audience": "Développeurs", "rationale": "Comprendre une protection concrète.",
                        "context": "Le propos présente une procédure et sa limite.", "essential_nuance": "Le test ne remplace pas la revue.",
                        "format": "horizontal", "platforms": ["youtube", "linkedin"], "risks": []})
        elif role == "title_support":
            supported = data["title_to_verify"] != self.unsupported_title
            result = {"supported": supported, "evidence_index": schema['properties']['evidence_index']['enum'][0], "reason": "Citation du double explicite."}
        elif role == 'cut_boundaries':
            result = {'start_status':'intact','end_status':'truncated' if self.incomplete_edges_title else 'intact','reason':'Bords de la fixture explicitement contrôlés.'}
        elif role == 'cut_boundary_blind_check':
            result={'verdict':'truncated','reason':'Le double confirme le fragment incomplet.'}
        elif role == "boundary_refinement":
            result = {k: data["proposal"][k] for k in ("title", "context", "essential_nuance")}
            result.update(start_anchor=data["current_start_anchor"], end_anchor=data["current_end_anchor"], quote_anchor=data["current_start_anchor"])
            result.update(usable=True, reason="Bornes synthétiques du double de test.")
        elif role == "concept_plan":
            result = {"concepts": [{"concept_index": i, "spoken_unit_index": data["spoken_units"][i%len(data["spoken_units"])]["index"],
                "anchor_term": autonomy.anchor_words(data["spoken_units"][i%len(data["spoken_units"])]["text"])[0],
                "focus": "Idée de recette "+str(i), "viewer_question": "Question de recette "+str(i)+" ?",
                "hypothesis": "Hypothèse synthétique "+str(i)} for i in range(3)]}
            result['concepts']=[{k:v for k,v in row.items() if k in schema['properties']['concepts']['items']['properties']} for row in result['concepts']]
        elif role == "citation_alignment":
            result = {"assignments": [{"concept_index": i,
                "spoken_unit_index": next(u["index"] for u in data["spoken_units"] if not data["concepts"][i].get("anchor_term") or data["concepts"][i]["anchor_term"] in autonomy.anchor_words(u["text"])),
                "supported": not self.unsupported_evidence, "reason": "Association synthétique du double de test."} for i in range(3)]}
        elif role == "packaging_concept":
            plan = data["plan"]
            result = {"angle": 'Angle de fixture', "hypothesis": 'Hypothèse de fixture',
                'anchor_term':data['allowed_anchor_terms'][0],
                "video_title": data['allowed_anchor_terms'][0].capitalize()+" : une méthode de contrôle "+str(plan["concept_index"]+1),
                "thumbnail_text": ["Avant de publier", "Garder les réserves", "Relire le contexte"][plan["concept_index"]],
                "wording_reason": "Ces mots restent dans le propos.", "title_image_complementarity": "La phrase précise un enjeu.",
                "visual_rationale": "Image de recette.", "frame_index": 0, "spoken_unit_index": data["spoken_unit"]["index"]}
            result = {k: v for k, v in result.items() if k in schema["properties"]}
        elif role == "packaging":
            result = {"preferred_index": 0}
        elif role == "thumbnail_crop_selection":
            result = {"index": 0, "usable": True, "reason": "Cadrage du double de test."}
        else:
            if role == "selection_review" and data["candidate"]["title"] == "Variante déjà couverte":
                raise AssertionError("An already retained overlapping alternative must be archived before expensive review")
            failed = role == "render_review" and data["candidate"]["title"] == self.reject_title
            result = {name: {"passed": not failed, "reason": "Image synthétique examinée par un double de test."} for name in schema["required"]}
            if self.reject_packaging_language and "french_language" in result:
                result["french_language"] = {"passed": False, "reason": "Le titre et la phrase d'image sont en anglais pour le public francophone."}
            if role == 'thumbnail_review' and self.reject_packaging_hypothesis and data['target_concept'].get('hypothesis'):
                result['faithfulness'] = {'passed':False,'reason':'Hypothèse causale absente des propos malgré un titre prudent.'}
        local_models.validate(result, schema)
        if validator:
            validator(result)
        self.directory.mkdir(parents=True, exist_ok=True)
        receipt = self.directory / (digest({"role": role, "data": data})+".json")
        autonomy.write_json(receipt, {"role": role, "response": result, "test_double": True})
        return result, {"path": str(receipt), "sha256": fingerprint(receipt), "model": {"name": "test-double"}, "cache": "miss"}


def image_double(source, directory, ranges, interval):
    from PIL import Image, ImageDraw
    directory.mkdir(parents=True, exist_ok=True)
    result = []
    for start, end in ranges:
        path = directory / (digest({"source": str(source), "range": [start, end]})+".jpg")
        if not path.exists():
            image = Image.new("RGB", (640, 360), "#357ca0")
            ImageDraw.Draw(image).text((30, 30), "SOURCE SYNTHETIQUE", fill="white")
            image.save(path)
        result.append({"path": str(path), "sha256": fingerprint(path), "time_seconds": (start+end)/2, "scope": "point_sample"})
    return result


def extract_double(arguments):
    from PIL import Image
    Image.new("RGB", (640, 360), "#357ca0").save(arguments[-1])
    return ""


def render_double(store, config, episode_id, segment_id, format_name, *, now=None):
    from youtube_growth.factory.packaging import prepare
    candidate = store.get("candidate", segment_id)
    episode = store.get("episode", episode_id)
    caption_version=candidate.get('caption_grouping_version',1)
    render_key = digest({"source": episode["source_sha256"], "cuts": candidate["cuts"], "format": format_name,'caption_grouping_version':caption_version})[:20]
    directory = store.directory / "test-renders" / segment_id / render_key
    directory.mkdir(parents=True, exist_ok=True)
    path, subtitles = directory / "video.mp4", directory / "subtitles.srt"
    path.write_bytes(b"synthetic-render-"+segment_id.encode()+render_key.encode())
    subtitles.write_text("1\n00:00:00,000 --> 00:00:10,000\nUne preuve conserve son contexte.\n", encoding="utf-8")
    ass=directory/'subtitles.ass';ass.write_text('[Script Info]\n; fixture explicite\n',encoding='utf-8')
    length = candidate["end_seconds"]-candidate["start_seconds"]
    asset = {"asset_id": "asset-"+segment_id+"-"+render_key, "episode_id": episode_id, "segment_id": segment_id,
             'parameters':{'layout':'fit_preserve_all_pixels_local_captions_v1','subtitle_grouping_version':caption_version},
             "source_sha256": episode["source_sha256"], "path": str(path), "sha256": fingerprint(path),
             "subtitle_path": str(subtitles), "subtitle_sha256": fingerprint(subtitles),
             'ass_path':str(ass),'ass_sha256':fingerprint(ass),
             "format": format_name, "duration_seconds": length, "qa_status": "needs_review",
             "qa": {"technical": "passed", "subtitle_boundary_warnings": [], "details": {"decode": "passed"}},
             "cuts": [{"source_start_seconds": candidate["start_seconds"], "source_end_seconds": candidate["end_seconds"],
                       "output_start_seconds": 0, "output_end_seconds": length}], "synthetic": True}
    store.put("asset", asset["asset_id"], asset, episode_id=episode_id, now=now)
    for pack in prepare(episode, candidate, asset, config, directory / "packs"):
        store.save_publication(pack, now=now)
    return asset


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "master.mp4"
        self.source.write_bytes(b"synthetic-owned-master")
        self.transcript = self.root / "transcript.json"
        autonomy.write_json(self.transcript, {"source_sha256": fingerprint(self.source), "segments": [
            {"start": i*10, "end": (i+1)*10, "text": text} for i, text in enumerate([
                "Nous vérifions les sources avant diffusion.", "Une preuve ne remplace pas toutes les revues.",
                "Une coupe doit conserver son contexte.", "Les réserves font partie du propos."])]})
        self.config = load_config()
        self.config["inbox_directory"] = str(self.root / "inbox")
        self.config["thumbnails"].update(width=1280, height=720)
        self.store = Store(self.root / "state")
        self.addCleanup(self.store.close)
        ModelDouble.reject_title, ModelDouble.empty, ModelDouble.unsupported_evidence = None, False, False
        ModelDouble.overlapping_alternative = False
        ModelDouble.unsupported_title = None
        ModelDouble.incomplete_edges_title = None
        ModelDouble.reject_packaging_language = False
        ModelDouble.reject_packaging_hypothesis = False
        for target, replacement in [("youtube_growth.factory.runtime.render_candidate", render_double),
            ("youtube_growth.factory.autonomy.Ollama", ModelDouble),
            ("youtube_growth.factory.autonomy.samples", image_double),
            ("youtube_growth.factory.local_faces.face_proposals", lambda frame: ([{"face_box": [200,100,70,70], "crop_pixels": [150,50,168,168], "image_size": [640,360]}], {"frame": frame, "scope": "test_double"})),
            ("youtube_growth.factory.autonomy.audio_correspondence", lambda *_: {"passed": True, "scope": "test_double"}),
            ("youtube_growth.shorts._call", extract_double),
            ("youtube_growth.factory.media.probe", lambda *_: {"duration_seconds": 40, "streams": []})]:
            p = patch(target, replacement)
            p.start()
            self.addCleanup(p.stop)

    def prepare(self, **kwargs):
        return autonomy.prepare_master(self.store, self.config, self.source, episode_id="local-test", title=kwargs.pop("title", "Recette locale"),
            transcript=self.transcript, publication_at=kwargs.pop("publication_at", "2026-10-29T09:00:00+01:00"),
            next_filming_at=kwargs.pop("next_filming_at", "2026-11-02T18:00:00+01:00"), synthetic=True, now=NOW, **kwargs)

    def drain(self):
        for _ in range(60):
            result = runtime.run_once(self.store, self.config, now=NOW)
            if result["status"] == "idle":
                return
        self.fail("La chaîne locale n'atteint pas un état stable.")

    def revision_plan(self, changes):
        episode = self.store.get("episode", "local-test")
        path = self.root / "revision.json"
        autonomy.write_json(path, {"version": 1, "episode_id": "local-test", "source_sha256": episode["source_sha256"],
            "transcript_sha256": episode["transcript_sha256"], "reviewer": "test-reader", "scope": "Explicit fixture review",
            "human_listening": False, "changes": changes})
        return path

    def independent_report(self,bundle):
        from youtube_growth.factory.thumbnails import CHECKS
        row={'bundle_id':bundle['bundle_id'],'content_digest':bundle['content_digest'],'source_sha256':bundle['source_sha256'],
            'asset_sha256':bundle['asset_sha256'],'status':'passed','scope':'images_and_text_only','human_listening':False,
            'blocking_findings':[],'checks':{name:True for name in CHECKS},
            'opened_files':[a['path'] for a in bundle['artifacts'] if a['kind'] in {'thumbnail','preview_320','preview_160','comparison'}]}
        path=self.root/(bundle['bundle_id']+'-independent.json')
        autonomy.write_json(path,{'reviewer':'independent-test-reader','bundles':[row]})
        return path

    def test_independent_image_review_preserves_model_refusal_and_never_attests_audio(self):
        ModelDouble.reject_packaging_hypothesis=True
        self.prepare();self.drain();receipts={}
        for asset in self.store.records('asset'):
            bundle=next(b for b in self.store.records('thumbnail_bundle') if b['asset_sha256']==asset['sha256'])
            receipts[bundle['receipt_path']]=fingerprint(Path(bundle['receipt_path']))
            result=local_review.adopt_packaging(self.store,self.config,bundle['bundle_id'],self.independent_report(bundle),now=NOW)
            self.assertFalse(result['human_listening'])
            adopted=self.store.get('thumbnail_bundle',bundle['bundle_id'])
            self.assertEqual(adopted['review_status'],'passed');self.assertFalse(adopted['local_review']['passed'])
            self.assertEqual(self.store.get('asset',asset['asset_id'])['qa_status'],'local_passed')
            repeated=local_review.adopt_packaging(self.store,self.config,bundle['bundle_id'],self.root/(bundle['bundle_id']+'-independent.json'),now=NOW)
            self.assertEqual(repeated['status'],'already_adopted')
        self.drain()
        self.assertEqual(self.store.get('local_calendar','local-test')['status'],'completed')
        self.assertTrue(all(p['status']=='local_ready' and not p.get('remote_id') and not p.get('scheduled_at') for p in self.store.publications()))
        self.assertFalse(any(j['kind']=='dispatch' for j in self.store.jobs()))
        for path,sha in receipts.items():self.assertEqual(fingerprint(Path(path)),sha)

    def test_independent_review_requires_all_current_images_checks_and_distinct_reader(self):
        self.prepare();self.drain();bundle=self.store.records('thumbnail_bundle')[0]
        path=self.independent_report(bundle);original=json.loads(path.read_text(encoding='utf-8'))
        for fault in ('image','criterion','source','reader'):
            report=copy.deepcopy(original)
            if fault=='image':report['bundles'][0]['opened_files'][0]='not-an-inspected-current-image.jpg'
            if fault=='criterion':report['bundles'][0]['checks']['content_fidelity']=False
            if fault=='source':report['bundles'][0]['source_sha256']='changed'
            if fault=='reader':report['reviewer']=bundle['created_by']
            autonomy.write_json(path,report)
            with self.subTest(fault=fault),self.assertRaises((ValueError,local_models.LocalModelError)):
                local_review.adopt_packaging(self.store,self.config,bundle['bundle_id'],path,now=NOW)
        self.assertNotIn('independent_local_review',self.store.get('thumbnail_bundle',bundle['bundle_id']))
        autonomy.write_json(path,original)
        pack=next(p for p in self.store.publications() if p['asset_sha256']==bundle['asset_sha256'])
        pack['remote_id']='already-published';self.store.save_publication(pack);before=copy.deepcopy(self.store.publication(pack['id']))
        with self.assertRaisesRegex(ValueError,'intention distante'):
            local_review.adopt_packaging(self.store,self.config,bundle['bundle_id'],path,now=NOW)
        self.assertEqual(self.store.publication(pack['id']),before)

    def test_modified_independent_report_invalidates_calendar(self):
        self.prepare();self.drain();bundle=self.store.records('thumbnail_bundle')[0]
        asset_id=next(a['asset_id'] for a in self.store.records('asset') if a['sha256']==bundle['asset_sha256'])
        path=self.independent_report(bundle)
        local_review.adopt_packaging(self.store,self.config,bundle['bundle_id'],path,now=NOW)
        report=json.loads(path.read_text(encoding='utf-8'));report['bundles'][0]['blocking_findings']=['New objection.']
        autonomy.write_json(path,report);self.drain()
        calendar=self.store.get('local_calendar','local-test')
        self.assertTrue(calendar['blocked'])
        self.assertFalse(any(p['asset_id']==asset_id for p in calendar['planned']))

    def test_packaging_upgrade_revokes_old_calendar_until_fresh_review(self):
        self.prepare(); self.drain()
        old_job = next(j for j in self.store.jobs() if j['kind'] == 'local_thumbnails')
        self.store.db.execute("UPDATE jobs SET status='blocked',last_error='old_packaging_refused' WHERE id=?", (old_job['id'],))
        with patch.object(autonomy, 'PACKAGING_VERSION', autonomy.PACKAGING_VERSION+1):
            autonomy.advance(self.store, self.config, now=NOW)
            self.assertEqual(next(j for j in self.store.jobs() if j['id'] == old_job['id'])['status'], 'cancelled')
            self.assertEqual(self.store.get('local_calendar', 'local-test')['planned'], [])
            self.assertTrue(any(j['kind'] == 'local_thumbnails' and j['status'] == 'queued' for j in self.store.jobs()))
            # Reuse compatible files, but never the old packaging approval.
            self.drain()
            self.assertTrue(all(p['local_packaging_version'] == autonomy.PACKAGING_VERSION for p in self.store.publications('local-test')))
            self.assertTrue(self.store.get('local_calendar', 'local-test')['planned'])

    def test_packaging_feedback_revokes_dates_and_preserves_approved_media_and_history(self):
        self.prepare();self.drain()
        asset=self.store.records('asset')[0]; original_hash=fingerprint(Path(asset['path']))
        bundle=next(b for b in self.store.records('thumbnail_bundle') if b['asset_sha256']==asset['sha256'])
        receipt=Path(bundle['receipt_path']);receipt_hash=fingerprint(receipt)
        self.assertTrue(self.store.get('local_calendar','local-test')['planned'])
        result=autonomy.request_packaging_revision(self.store,self.config,asset['asset_id'],'independent-reader',
            ['La question doit annoncer la discussion sans imposer une réponse.'],now=NOW)
        duplicate=autonomy.request_packaging_revision(self.store,self.config,asset['asset_id'],'independent-reader',
            ['La question doit annoncer la discussion sans imposer une réponse.'],now=NOW)
        self.assertEqual(result['job_id'],duplicate['job_id']);self.assertEqual(duplicate['status'],'already_requested')
        self.assertFalse(self.store.get('local_calendar','local-test')['planned'])
        self.assertEqual(self.store.get('asset',asset['asset_id'])['qa_status'],'local_passed')
        self.assertEqual(self.store.get('thumbnail_bundle',bundle['bundle_id'])['review_status'],'superseded')
        self.drain()
        self.assertEqual(fingerprint(Path(asset['path'])),original_hash)
        self.assertEqual(fingerprint(receipt),receipt_hash)
        new=next(b for b in self.store.records('thumbnail_bundle') if b['asset_sha256']==asset['sha256'] and b['review_status']=='local_passed')
        brief=json.loads(Path(new['brief_path']).read_text(encoding='utf-8'))
        self.assertEqual(brief['review_feedback']['reviewer'],'independent-reader')
        self.assertNotEqual(new['bundle_id'],bundle['bundle_id'])
        self.assertTrue(self.store.get('local_calendar','local-test')['planned'])

    def test_packaging_feedback_and_worker_preserve_remote_intent(self):
        self.prepare();self.drain()
        pack=self.store.publications()[0];pack['remote_id']='existing-remote-receipt';self.store.save_publication(pack)
        before=copy.deepcopy(self.store.publication(pack['id']))
        with self.assertRaisesRegex(ValueError,'intention distante'):
            autonomy.request_packaging_revision(self.store,self.config,pack['asset_id'],'reader',['Un changement local.'],now=NOW)
        episode=self.store.get('episode','local-test')
        with self.assertRaisesRegex(local_models.LocalModelError,'remote_intent'):
            autonomy.thumbnails(self.store,episode,self.config,{'payload':autonomy.payload(episode,self.config,
                asset_id=pack['asset_id'],packaging_version=autonomy.PACKAGING_VERSION,quality_version=autonomy.QUALITY_VERSION)},now=NOW)
        self.assertEqual(self.store.publication(pack['id']),before)

    def test_real_thumbnail_job_waits_for_finished_artwork_before_model_calls(self):
        self.prepare(); self.drain()
        episode = self.store.get('episode', 'local-test')
        episode['synthetic'] = False
        asset = self.store.records('asset')[0]
        job = {'payload': autonomy.payload(episode, self.config, asset_id=asset['asset_id'],
                packaging_version=autonomy.PACKAGING_VERSION, quality_version=autonomy.QUALITY_VERSION)}
        with patch.object(autonomy, '_model', side_effect=AssertionError('No model before artwork')):
            with self.assertRaisesRegex(local_models.LocalModelError, 'local_finished_artwork_required'):
                autonomy.thumbnails(self.store, episode, self.config, job, now=NOW)

    def test_real_thumbnail_worker_imports_finished_artwork_and_keeps_local_review(self):
        from PIL import Image
        self.prepare(); self.drain()
        episode = self.store.get('episode', 'local-test')
        episode['synthetic'] = False
        asset = self.store.records('asset')[0]
        previous = next(b for b in self.store.records('thumbnail_bundle') if b['asset_sha256'] == asset['sha256'])
        brief = json.loads(Path(previous['brief_path']).read_text(encoding='utf-8'))
        brief['created_by'] = 'artist-alice'
        directory = autonomy._directory(self.store, episode) / 'finished-artwork' / asset['asset_id']
        directory.mkdir(parents=True)
        for reference in brief['benchmark']['references']:
            reference.pop('synthetic', None)
        for index, concept in enumerate(brief['concepts']):
            concept.pop('anchor_term', None)
            image = directory / ('art-'+str(index)+'.png')
            Image.new('RGB', (1280, 720), (210, 60+index*40, 45)).save(image)
            concept.update(art_direction='Fixture éditoriale.', visual_story='Objet illustré de test.',
                typography_reason='Lettrage déjà intégré.', image_box=[0, 0, 1280, 720], text_box=[30, 30, 500, 200])
            concept['image'] = {'kind':'finished_artwork', 'path':image.name, 'sha256':fingerprint(image),
                'rights_evidence':'Fixture synthétique temporaire.', 'subject_identity':'Aucune personne.',
                'crop':[0, 0, 1, 1], 'focus_box':[.2, .3, .4, .3]}
        autonomy.write_json(directory / 'brief.json', brief)
        job = {'episode_id':episode['episode_id'], 'payload':autonomy.payload(episode, self.config, asset_id=asset['asset_id'],
            packaging_version=autonomy.PACKAGING_VERSION, quality_version=autonomy.QUALITY_VERSION)}
        with patch.object(autonomy, 'portrait_frame', side_effect=AssertionError('No template portrait')):
            result = autonomy.thumbnails(self.store, episode, self.config, job, now=NOW)
        self.assertEqual(result['status'], 'local_passed')
        bundle = self.store.get('thumbnail_bundle', result['bundle_id'])
        self.assertFalse(bundle['synthetic'])
        self.assertTrue(bundle['local_review']['passed'])
        self.assertEqual(bundle['created_by'], 'artist-alice')
        from youtube_growth.factory.thumbnails import review_bundle, CHECKS
        with self.assertRaises(ValueError):
            review_bundle(bundle, reviewer='artist-alice', evidence='Self-review', checks=sorted(CHECKS), now=NOW)
        exported = Image.open(bundle['variants'][0]['thumbnail']['path'])
        self.assertLess(sum(abs(a-b) for a,b in zip(exported.getpixel((5, 5)), (210, 60, 45))), 15)

    def test_quality_upgrade_rechecks_media_without_repeating_compatible_packaging(self):
        self.prepare(); self.drain()
        thumbs = len(self.store.records('thumbnail_bundle'))
        with patch.object(autonomy,'QUALITY_VERSION',autonomy.QUALITY_VERSION+1):
            autonomy.advance(self.store,self.config,now=NOW)
            self.assertEqual(self.store.get('local_calendar','local-test')['planned'],[])
            self.assertTrue(any(j['kind']=='local_quality' and j['status']=='queued' for j in self.store.jobs()))
            self.drain()
            self.assertTrue(all(a['local_quality_version']==autonomy.QUALITY_VERSION for a in self.store.records('asset')))
            self.assertTrue(self.store.get('local_calendar','local-test')['planned'])
            self.assertEqual(len(self.store.records('thumbnail_bundle')),thumbs)

    def test_metadata_revision_never_reactivates_a_superseded_render(self):
        self.prepare();self.drain()
        first=self.store.records('asset')[0]
        plan=self.revision_plan([{'segment_id':first['segment_id'],'action':'revise','start_seconds':0,'end_seconds':30,'reason':'Étendre la coupe de fixture.'}])
        immutable=self.root/'revision-one.json';plan.rename(immutable)
        self.store.set_setting('paused',True);local_revisions.apply_plan(self.store,self.config,immutable,now=NOW)
        self.store.set_setting('paused',False);self.drain()
        historical=copy.deepcopy(self.store.get('asset',first['asset_id']))
        self.assertEqual(historical['qa_status'],'superseded')
        second=self.revision_plan([{'segment_id':first['segment_id'],'action':'revise','context':'Contexte corrigé de la fixture.','reason':'Corriger les rôles décrits.'}])
        self.store.set_setting('paused',True);local_revisions.apply_plan(self.store,self.config,second,now=NOW)
        self.store.set_setting('paused',False);self.drain()
        self.assertEqual(self.store.get('asset',first['asset_id']),historical)
        current=[a for a in self.store.records('asset') if a['segment_id']==first['segment_id'] and a['qa_status']!='superseded']
        self.assertEqual(len(current),1);self.assertEqual(current[0]['qa_status'],'local_passed')

    def test_caption_profile_upgrade_revokes_dates_and_keeps_original_files(self):
        self.prepare(); self.drain()
        old=self.store.records('asset')[0]; sha=fingerprint(Path(old['path']))
        # Seed the historical job shape used before render profiles existed.
        for job in self.store.jobs():
            if job['kind']=='local_render' and job['payload'].get('segment_id')==old['segment_id']:
                self.store.db.execute('DELETE FROM jobs WHERE id=?',(job['id'],))
                legacy={k:v for k,v in job['payload'].items() if k!='render_profile'}
                identity=self.store.enqueue('local_render','local-test',legacy,now=NOW)
                self.store.db.execute("UPDATE jobs SET status='completed' WHERE id=?",(identity,))
        old['parameters']['layout']='legacy_overlay'
        self.store.put('asset',old['asset_id'],old,episode_id='local-test')
        autonomy.advance(self.store,self.config,now=NOW)
        self.assertEqual(self.store.get('asset',old['asset_id'])['qa_status'],'superseded')
        self.assertEqual(fingerprint(Path(old['path'])),sha)
        self.assertEqual(self.store.get('local_calendar','local-test')['planned'],[])
        self.assertTrue(any(j['kind']=='local_render' and j['status']=='queued' and j['payload'].get('render_profile')==autonomy.RENDER_PROFILE for j in self.store.jobs()))

    def test_changed_ass_file_invalidates_calendar_even_if_burned_video_is_unchanged(self):
        self.prepare();self.drain()
        asset=self.store.records('asset')[0]
        Path(asset['ass_path']).write_text('changed caption source',encoding='utf-8')
        autonomy.advance(self.store,self.config,now=NOW);self.drain()
        calendar=self.store.get('local_calendar','local-test')
        self.assertTrue(calendar['blocked'])
        self.assertFalse(any(p['asset_id']==asset['asset_id'] for p in calendar['planned']))

    def test_caption_only_revision_creates_new_export_without_changing_source_cut(self):
        self.prepare();self.drain()
        old=self.store.records('asset')[0];source_hash=fingerprint(Path(old['path']))
        candidate=self.store.get('candidate',old['segment_id']);bounds=(candidate['start_seconds'],candidate['end_seconds'])
        path=self.revision_plan([{'segment_id':old['segment_id'],'action':'revise','caption_grouping_version':2,'reason':'Le mot final doit rester lisible.'}])
        self.store.set_setting('paused',True);local_revisions.apply_plan(self.store,self.config,path,now=NOW)
        self.store.set_setting('paused',False);self.drain()
        new=next(a for a in self.store.records('asset') if a['segment_id']==old['segment_id'] and a['qa_status']=='local_passed')
        self.assertNotEqual(new['path'],old['path'])
        self.assertEqual(new['parameters']['subtitle_grouping_version'],2)
        self.assertEqual(fingerprint(Path(old['path'])),source_hash)
        current=self.store.get('candidate',old['segment_id'])
        self.assertEqual((current['start_seconds'],current['end_seconds']),bounds)

    def test_incomplete_literal_edges_block_packaging_even_when_title_is_supported(self):
        ModelDouble.incomplete_edges_title = 'explicit test refusal'
        self.prepare(); self.drain()
        self.assertTrue(all(a['qa_status']=='local_failed' for a in self.store.records('asset')))
        self.assertFalse(self.store.records('thumbnail_bundle'))
        self.assertTrue(all(not a['local_quality']['boundaries']['passed'] for a in self.store.records('asset')))

    def test_thumbnail_critic_gets_own_evidence_without_creator_attestations(self):
        original = ModelDouble.complete
        calls = []
        def recorded(client, role, prompt, data, schema, **kwargs):
            calls.append((role, copy.deepcopy(data)))
            return original(client, role, prompt, data, schema, **kwargs)
        with patch.object(ModelDouble, 'complete', recorded):
            self.prepare(); self.drain()
        reviews = [d for role, d in calls if role == 'thumbnail_review']
        self.assertTrue(reviews)
        for data in reviews:
            self.assertNotIn('candidate', data)
            self.assertNotIn('alternative_concepts', data)
            self.assertTrue(data['target_concept']['hypothesis'])
            self.assertTrue(data['target_concept']['angle'])
            self.assertEqual({e['evidence_id'] for e in data['content_evidence']}, set(data['target_concept']['evidence_ids']))
        comparisons = [d for role, d in calls if role == 'thumbnail_comparison']
        self.assertTrue(all(len(d['concepts']) == 3 for d in comparisons))

    def test_language_refusal_blocks_faithful_packaging_and_calendar_without_rejecting_media(self):
        ModelDouble.reject_packaging_language = True
        self.prepare(); self.drain()
        self.assertTrue(all(a['qa_status'] == 'local_passed' for a in self.store.records('asset')))
        bundles = self.store.records('thumbnail_bundle')
        self.assertTrue(bundles)
        for bundle in bundles:
            self.assertIn(bundle['review_status'], {'local_failed', 'superseded'})
            if bundle['review_status'] == 'superseded':
                self.assertEqual(bundle['previous_review_status'], 'local_failed')
            checks = [b['checks'] for b in bundle['local_review']['batches']]
            self.assertTrue(all(c.get('faithfulness', {'passed': True})['passed'] for c in checks))
            self.assertTrue(any(not c['french_language']['passed'] for c in checks if 'french_language' in c))
        self.assertFalse(any(p['status'] == 'local_ready' for p in self.store.publications()))
        self.assertFalse(self.store.get('local_calendar', 'local-test')['planned'])

    def test_new_portrait_or_title_cannot_disguise_a_repeated_thumbnail_phrase(self):
        previous = {'angle':'Autonomie', 'hypothesis':'Les outils donnent une autonomie.',
                    'video_title':'Agent : outils et autonomie', 'thumbnail_text':'Agent, outils, autonomie'}
        alternative = {'angle':'Débat', 'hypothesis':'La frontière des agents.',
                       'video_title':'Bot ou agent : la frontière', 'thumbnail_text':'Agent, outils, autonomie'}
        with self.assertRaisesRegex(ValueError, 'recopies un concept'):
            autonomy.validate_local_wording({'concepts':[alternative]}, self.config, prior_concepts=[previous])

    def test_unsupported_hypothesis_reaches_critic_and_blocks_otherwise_usable_thumbnail(self):
        ModelDouble.reject_packaging_hypothesis=True
        self.prepare();self.drain()
        self.assertTrue(all(a['qa_status']=='local_passed' for a in self.store.records('asset')))
        bundles=self.store.records('thumbnail_bundle');self.assertTrue(bundles)
        for bundle in bundles:
            self.assertFalse(bundle['local_review']['passed'])
            checks=[batch['checks'] for batch in bundle['local_review']['batches']]
            self.assertTrue(any(not c['faithfulness']['passed'] for c in checks if 'faithfulness' in c))
            self.assertTrue(all(c['french_language']['passed'] for c in checks if 'french_language' in c))
        self.assertFalse(any(p['status']=='local_ready' for p in self.store.publications()))
        self.assertFalse(self.store.get('local_calendar','local-test')['planned'])

    def test_linkedin_handoff_matches_reviewed_text_cover_and_local_calendar(self):
        self.prepare(); self.drain()
        calendar = self.store.get('local_calendar','local-test')
        for pack in self.store.publications('local-test'):
            manifest = json.loads(Path(pack['pack_path']).read_text(encoding='utf-8'))
            self.assertEqual(manifest, {k:v for k,v in pack.items() if k != 'updated_at'})
            self.assertIsNone(pack['scheduled_at'])
            self.assertEqual(pack['proposed_at'], next(p['proposed_at'] for p in calendar['planned'] if p['publication_id'] == pack['id']))
            if pack['platform'] == 'linkedin':
                directory = Path(pack['manual_pack'])
                self.assertEqual(directory,Path(pack['pack_path']).parent)
                self.assertEqual(fingerprint(directory/'video.mp4'),pack['asset_sha256'])
                self.assertEqual(fingerprint(directory/'cover.jpg'),pack['cover_sha256'])
        pack = next(p for p in self.store.publications('local-test') if p['platform'] == 'linkedin')
        directory = Path(pack['manual_pack'])
        old = (directory/'pack.json').read_bytes()
        (directory/'texte.txt').write_text('tampered',encoding='utf-8')
        self.drain()
        blocked = self.store.get('local_calendar','local-test')['blocked']
        self.assertTrue(any(p['publication_id'] == pack['id'] for p in blocked))
        self.assertEqual((directory/'pack.json').read_bytes(),old)

    def test_editorial_archive_revokes_calendar_without_deleting_media_and_is_idempotent(self):
        self.prepare(); self.drain()
        candidate = next(c for c in self.store.records("candidate") if c["title"] == "Contrôler les sources")
        files = {a["path"]: fingerprint(Path(a["path"])) for a in self.store.records("asset")}
        path = self.revision_plan([{"segment_id": candidate["segment_id"], "action": "archive", "reason": "Titre non soutenu par les paroles."}])
        self.store.set_setting("paused", True)
        local_revisions.apply_plan(self.store, self.config, path, now=NOW)
        self.assertTrue(all(b['review_status']=='superseded' for b in self.store.records('thumbnail_bundle') if b['segment_id']==candidate['segment_id']))
        count = len(self.store.jobs())
        self.assertEqual(local_revisions.apply_plan(self.store, self.config, path, now=NOW)["status"], "already_applied")
        self.assertEqual(len(self.store.jobs()), count)
        self.store.set_setting("paused", False); self.drain()
        self.assertEqual(len(self.store.get("local_calendar", "local-test")["planned"]), 2)
        self.assertTrue(all(Path(p).exists() and fingerprint(Path(p)) == sha for p, sha in files.items()))

    def test_revised_cut_keeps_old_export_and_rechecks_before_new_calendar(self):
        self.prepare(); self.drain()
        candidate = next(c for c in self.store.records("candidate") if c["title"] == "Contrôler les sources")
        old = next(a for a in self.store.records("asset") if a["segment_id"] == candidate["segment_id"])
        path = self.revision_plan([{"segment_id": candidate["segment_id"], "action": "revise", "reason": "Inclure la réserve.",
                                  "start_seconds": 10, "end_seconds": 30}])
        self.store.set_setting("paused", True); local_revisions.apply_plan(self.store, self.config, path, now=NOW)
        self.assertEqual(self.store.get("asset", old["asset_id"])["qa_status"], "superseded")
        self.store.set_setting("paused", False); self.drain()
        current = [a for a in self.store.records("asset") if a["segment_id"] == candidate["segment_id"] and a["qa_status"] == "local_passed"]
        self.assertEqual(len(current), 1)
        self.assertNotEqual(current[0]["asset_id"], old["asset_id"])
        self.assertEqual(fingerprint(Path(old["path"])), old["sha256"])
        self.assertTrue(any(j["kind"] == "local_recheck" and j["status"] == "completed" for j in self.store.jobs()))
        self.assertFalse(any(j["kind"] == "dispatch" for j in self.store.jobs()))

    def test_revision_refuses_wrong_source_and_published_intents(self):
        self.prepare(); self.drain()
        candidate = self.store.records("candidate")[0]
        path = self.revision_plan([{"segment_id": candidate["segment_id"], "action": "archive", "reason": "Revue."}])
        self.store.set_setting("paused", True)
        data = json.loads(path.read_text()); data["source_sha256"] = "wrong"; autonomy.write_json(path, data)
        with self.assertRaises(ValueError):local_revisions.apply_plan(self.store, self.config, path, now=NOW)
        path = self.revision_plan([{"segment_id": candidate["segment_id"], "action": "archive", "reason": "Revue."}])
        pack = next(p for p in self.store.publications() if p["segment_id"] == candidate["segment_id"])
        pack["remote_id"] = "an-existing-remote-result"; self.store.save_publication(pack)
        with self.assertRaises(ValueError):local_revisions.apply_plan(self.store, self.config, path, now=NOW)
        self.assertEqual(self.store.get("candidate", candidate["segment_id"])["decision"], "retained")

    def test_metadata_revision_reuses_video_but_requires_fresh_packaging(self):
        self.prepare(); self.drain()
        candidate = next(c for c in self.store.records("candidate") if c["title"] == "Contrôler les sources")
        old = next(a for a in self.store.records("asset") if a["segment_id"] == candidate["segment_id"])
        path = self.revision_plan([{"segment_id": candidate["segment_id"], "action": "revise", "reason": "Nuance corrigée.",
                                  "title": "Sources : la portée réelle des contrôles"}])
        self.store.set_setting("paused", True); local_revisions.apply_plan(self.store, self.config, path, now=NOW)
        self.store.set_setting("paused", False); self.drain()
        self.assertEqual(len(self.store.records("asset")), 2)
        self.assertEqual(self.store.get("local_calendar", "local-test")["status"], "completed")
        self.assertEqual(fingerprint(Path(old["path"])), old["sha256"])
        packs = [p for p in self.store.publications() if p["asset_id"] == old["asset_id"]]
        self.assertTrue(all(p["status"] == "local_ready" and p["packaging_status"] == "local_passed" for p in packs))
        jobs = [j for j in self.store.jobs() if j["kind"] == "local_thumbnails" and j["payload"].get("asset_id") == old["asset_id"]]
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all(j["status"] == "completed" for j in jobs))

    def test_master_to_thumbnails_and_conditional_calendar_without_any_dispatch(self):
        original = fingerprint(self.source)
        self.prepare()
        with patch("youtube_growth.factory.connectors.build_connector", side_effect=AssertionError("Aucun transport social")):
            self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["status"], "completed", calendar)
        self.assertEqual(len(calendar["planned"]), 4)
        self.assertTrue(calendar["conditional_on_episode_availability"])
        self.assertTrue(calendar["requires_destination"])
        self.assertFalse(calendar["valid_for_publication"])
        self.assertEqual(fingerprint(self.source), original)
        self.assertFalse(any(j["kind"] == "dispatch" for j in self.store.jobs()))
        self.assertEqual(len(self.store.records("asset")), 2)
        self.assertEqual(len(self.store.records("thumbnail_bundle")), 2)
        for bundle in self.store.records("thumbnail_bundle"):
            self.assertEqual(len(bundle["variants"]), 3)
            self.assertEqual(bundle["review_status"], "local_passed")
            self.assertFalse(bundle["local_review"]["human_review"])
            brief = json.loads(Path(bundle["brief_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(brief["content_evidence"]), 3)
            self.assertEqual(len({e["evidence_id"] for e in brief["content_evidence"]}), 3)
        for pack in self.store.publications():
            self.assertEqual(pack["status"], "local_ready")
            self.assertIsNone(pack["scheduled_at"])
            with self.assertRaisesRegex(ValueError, "local_only_publication_forbidden"):
                scheduler.assert_sendable(self.store, self.config, pack, now=NOW)

    def test_repeated_ingestion_and_worker_restart_do_not_duplicate_outputs(self):
        self.prepare()
        self.drain()
        jobs, assets = len(self.store.jobs()), len(self.store.records("asset"))
        self.prepare()
        self.drain()
        self.assertEqual(len(self.store.jobs()), jobs)
        self.assertEqual(len(self.store.records("asset")), assets)
        path = self.store.directory
        self.store.close()
        self.store = Store(path)
        self.addCleanup(self.store.close)
        self.drain()
        self.assertEqual(len(self.store.jobs()), jobs)

    def test_advancing_worker_clock_reaches_idle_and_preserves_calendar_reports(self):
        from datetime import timedelta
        from youtube_growth.factory.contracts import instant
        self.prepare()
        start = instant(NOW)
        for tick in range(60):
            result = runtime.run_once(self.store, self.config, now=start+timedelta(seconds=tick))
            if result['status'] == 'idle':
                break
        else:
            self.fail('Le calendrier se recrée sans fin lorsque le temps avance.')
        jobs = len(self.store.jobs())
        reports = {p: (fingerprint(p), p.stat().st_mtime_ns) for p in (self.store.directory/'reports').glob('*')}
        calendar = copy.deepcopy(self.store.get('local_calendar', 'local-test'))
        for offset in range(1, 6):
            result = runtime.run_once(self.store, self.config, now=start+timedelta(seconds=tick+offset))
            self.assertEqual(result['status'], 'idle')
        self.assertEqual(len(self.store.jobs()), jobs)
        self.assertEqual(self.store.get('local_calendar', 'local-test'), calendar)
        self.assertEqual({p: (fingerprint(p), p.stat().st_mtime_ns) for p in reports}, reports)
        # Crossing a real slot still invalidates the forecast; idle is not a frozen cache.
        later = start+timedelta(hours=2, minutes=1)
        for offset in range(10):
            result = runtime.run_once(self.store, self.config, now=later+timedelta(seconds=offset))
            if result['status'] == 'idle':
                break
        else:
            self.fail('Le nouveau créneau ne se stabilise pas.')
        revised = self.store.get('local_calendar', 'local-test')
        self.assertNotEqual(revised['planned'], calendar['planned'])
        self.assertTrue(all(instant(p['proposed_at']) >= later for p in revised['planned']))
        self.assertFalse(any(j['kind'] == 'dispatch' for j in self.store.jobs()))

    def test_calendar_ignores_sqlite_timestamp_but_rechecks_pack_status(self):
        from datetime import timedelta
        from youtube_growth.factory.contracts import instant
        self.prepare(); self.drain()
        jobs = len(self.store.jobs())
        pack = self.store.publications('local-test')[0]
        later = instant(NOW)+timedelta(seconds=30)
        self.store.save_publication(pack, now=later)
        self.assertEqual(runtime.run_once(self.store, self.config, now=later)['status'], 'idle')
        self.assertEqual(len(self.store.jobs()), jobs)
        pack['status'] = 'blocked'
        self.store.save_publication(pack, now=later)
        self.assertEqual(runtime.run_once(self.store, self.config, now=later)['kind'], 'local_calendar')
        calendar = self.store.get('local_calendar', 'local-test')
        self.assertTrue(any(p['publication_id'] == pack['id'] for p in calendar['blocked']))
        self.assertFalse(any(p['publication_id'] == pack['id'] for p in calendar['planned']))

    def test_failed_review_blocks_only_its_own_content(self):
        ModelDouble.reject_title = "Contrôler les sources"
        self.prepare()
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["status"], "partial")
        self.assertEqual(len(calendar["planned"]), 2)
        self.assertTrue(any(x["reason"] == "local_quality_failed" for x in calendar["stage_errors"]))

    def test_unsupported_title_blocks_packaging_even_when_audio_and_frames_are_valid(self):
        ModelDouble.unsupported_title = "Contrôler les sources"
        self.prepare(); self.drain()
        candidate = next(c for c in self.store.records("candidate") if c["title"] == ModelDouble.unsupported_title)
        asset = next(a for a in self.store.records("asset") if a["segment_id"] == candidate["segment_id"])
        self.assertEqual(asset["qa_status"], "local_failed")
        self.assertFalse(asset["local_quality"]["title_support"]["passed"])
        self.assertFalse(any(b["segment_id"] == candidate["segment_id"] for b in self.store.records("thumbnail_bundle")))
        self.assertEqual(len(self.store.get("local_calendar", "local-test")["planned"]), 2)

    def test_output_headroom_repair_preserves_old_file_and_rechecks_new_asset(self):
        def hot_render(*args, **kwargs):
            result = render_double(*args, **kwargs)
            candidate = self.store.get("candidate", result["segment_id"])
            if candidate["title"] == "Contrôler les sources":
                result["qa"].update(technical="needs_review", details={"decode": "passed", "max_volume_db": 0,
                                      "black_intervals_seconds": [], "silence_events": []})
            return result
        def repaired(asset):
            result = copy.deepcopy(asset)
            target = Path(asset["path"]).with_name("headroom.mp4")
            target.write_bytes(b"explicit-audio-repair-double")
            result.update(asset_id=asset["asset_id"]+"-headroom", path=str(target), sha256=fingerprint(target), audio_headroom={"gain_db": -1.5})
            result["qa"]["technical"] = "passed"
            return result
        with patch("youtube_growth.factory.runtime.render_candidate", side_effect=hot_render), \
             patch("youtube_growth.factory.local_audio.repair_headroom", side_effect=repaired) as repair:
            self.prepare(); self.drain()
        self.assertEqual(repair.call_count, 1)
        old = next(a for a in self.store.records("asset") if a.get("replacement_asset_id"))
        self.assertEqual(fingerprint(Path(old["path"])), old["sha256"])
        self.assertEqual(self.store.get("asset", old["replacement_asset_id"])["qa_status"], "local_passed")
        self.assertEqual(len(self.store.get("local_calendar", "local-test")["planned"]), 4)

    def test_overlapping_alternative_keeps_history_without_repeating_accepted_visual_review(self):
        ModelDouble.overlapping_alternative = True
        self.prepare()
        self.drain()
        candidates = self.store.records("candidate")
        archived = next(c for c in candidates if c["title"] == "Variante déjà couverte")
        self.assertEqual(archived["decision"], "archived")
        self.assertEqual(archived["local_editorial_review"]["scope"], "not_performed_already_retained_alternative")
        self.assertEqual(len(self.store.records("asset")), 2)

    def test_failed_legacy_headroom_upgrade_uses_original_not_already_encoded_repair(self):
        self.prepare(); self.drain()
        original = self.store.records('asset')[0]
        broken = copy.deepcopy(original)
        path = Path(original['path']).with_name('legacy-headroom.mp4'); path.write_bytes(b'legacy-headroom-fixture')
        broken.update(asset_id='legacy-headroom',path=str(path),sha256=fingerprint(path),qa_status='local_failed',
            audio_headroom={'gain_db':-1.5,'original_asset_id':original['asset_id'],'original_sha256':original['sha256']})
        broken['qa'].update(technical='needs_review',details={'decode':'passed','max_volume_db':0,'black_intervals_seconds':[],'silence_events':[]})
        self.store.put('asset',broken['asset_id'],broken,episode_id='local-test')
        original['qa_status']='superseded'
        self.store.put('asset',original['asset_id'],original,episode_id='local-test')
        def fixed(asset):
            self.assertEqual(asset['asset_id'],original['asset_id'])
            self.assertNotIn('audio_headroom',asset)
            result=copy.deepcopy(asset); target=path.with_name('measured-headroom.mp4');target.write_bytes(b'measured-fixture')
            result.update(asset_id='measured-headroom',path=str(target),sha256=fingerprint(target),qa_status='needs_review',
                audio_headroom={'version':2,'gain_db':-4.2,'original_asset_id':asset['asset_id'],'original_sha256':asset['sha256']})
            result['qa']['technical']='passed';result.pop('local_quality',None)
            return result
        with patch('youtube_growth.factory.local_audio.repair_headroom',side_effect=fixed) as repair:
            result=autonomy.quality(self.store,self.store.get('episode','local-test'),self.config,
                {'payload':{'asset_id':broken['asset_id'],'local_run_key':broken['local_run_key']}},now=NOW)
        self.assertEqual(repair.call_count,1)
        self.assertEqual(result['asset_id'],'measured-headroom')
        self.assertEqual(self.store.get('asset',broken['asset_id'])['qa_status'],'superseded')
        self.assertEqual(fingerprint(Path(original['path'])),original['sha256'])
    def test_unsupported_concept_is_blocked_even_when_media_quality_passed(self):
        ModelDouble.unsupported_evidence = True
        self.prepare()
        self.drain()
        self.assertTrue(all(a["qa_status"] == "local_passed" for a in self.store.records("asset")))
        calendar = self.store.get("local_calendar", "local-test")
        self.assertFalse(calendar["planned"])
        self.assertTrue(any(x["reason"] == "local_concept_not_supported_by_speech" for x in calendar["stage_errors"]))

    def test_missing_dates_do_not_prevent_media_but_block_calendar(self):
        self.prepare(publication_at=None, next_filming_at=None)
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["ready_packs"], 4)
        self.assertEqual(set(calendar["missing"]), {"planned_publication_at", "next_filming_at"})
        self.assertFalse(calendar["planned"])
        self.assertEqual(calendar["status"], "partial")

    def test_no_candidate_does_not_create_a_content_quota(self):
        ModelDouble.empty = True
        self.prepare()
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["status"], "completed")
        self.assertEqual(calendar["planned"], [])
        self.assertEqual(self.store.records("asset"), [])

    def test_modified_thumbnail_cannot_remain_on_the_calendar(self):
        self.prepare()
        self.drain()
        for bundle in self.store.records("thumbnail_bundle"):
            Path(bundle["variants"][0]["previews"][0]["path"]).write_bytes(b"changed")
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertFalse(calendar["planned"])
        self.assertEqual(len(calendar["blocked"]), 4)

    def test_modified_generation_proof_invalidates_the_calendar(self):
        self.prepare()
        self.drain()
        for bundle in self.store.records("thumbnail_bundle"):
            brief = json.loads(Path(bundle["brief_path"]).read_text(encoding="utf-8"))
            Path(brief["generation_evidence"]["concept_receipts"][0]["path"]).write_bytes(b"changed")
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertFalse(calendar["planned"])
        self.assertEqual(len(calendar["blocked"]), 4)

    def test_master_without_transcript_runs_transcription_then_all_local_stages(self):
        result = json.loads(self.transcript.read_text(encoding="utf-8"))
        with patch.object(autonomy, "transcribe", return_value=(result, {"model": {"test_double": True}, "cache": "miss"})) as recognizer:
            autonomy.prepare_master(self.store, self.config, self.source, episode_id="local-test", title="Recette depuis le master",
                publication_at="2026-10-29T09:00:00+01:00", next_filming_at="2026-11-02T18:00:00+01:00", synthetic=True, now=NOW)
            self.drain()
            self.assertEqual(recognizer.call_count, 1)
        episode = self.store.get("episode", "local-test")
        self.assertTrue(episode["local_generated_transcript"])
        self.assertEqual(self.store.get("local_calendar", "local-test")["status"], "completed")

    def test_missing_transcription_model_is_a_blocker_not_an_empty_success(self):
        with patch.object(autonomy, "transcribe", side_effect=local_models.LocalModelError("local_transcription_model_missing")):
            autonomy.prepare_master(self.store, self.config, self.source, episode_id="local-test", title="Master sans moteur",
                publication_at="2026-10-29T09:00:00+01:00", next_filming_at="2026-11-02T18:00:00+01:00", synthetic=True, now=NOW)
            self.drain()
        self.assertEqual(self.store.records("asset"), [])
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["status"], "blocked")
        self.assertEqual(calendar["stage_errors"][0]["reason"], "local_transcription_model_missing")

    def test_modified_master_invalidates_an_existing_calendar(self):
        self.prepare()
        self.drain()
        self.source.write_bytes(b"different source")
        self.drain()
        calendar = self.store.get("local_calendar", "local-test")
        self.assertEqual(calendar["status"], "blocked")
        self.assertTrue(calendar["stale"])
        self.assertFalse(calendar["planned"])

    def test_pause_does_not_run_local_compute(self):
        self.prepare()
        self.store.set_setting("paused", True)
        self.drain()
        self.assertEqual(self.store.records("asset"), [])
        self.store.set_setting("paused", False)
        self.drain()
        self.assertEqual(self.store.get("local_calendar", "local-test")["status"], "completed")

    def test_superseded_job_does_not_apply_old_selection(self):
        self.prepare()
        job = next(j for j in self.store.jobs() if j["kind"] == "local_transcribe")
        self.prepare(title="Nouveau titre")
        self.assertEqual(autonomy.execute(self.store, self.config, job, now=NOW), {"status": "superseded"})
        self.drain()
        self.assertEqual(self.store.get("local_calendar", "local-test")["revision"], self.store.get("episode", "local-test")["revision"])


class LocalModelContractTests(unittest.TestCase):
    def test_generated_question_must_be_complete_without_added_foreign_fragment(self):
        source='Nous discutons du suivi des agents et de leurs résultats.'
        for question in ('Comment suivre les agents dans la验', 'Comment suivre les agents dans la验 ?', 'Comment suivre le travail des agents dans la'):
            with self.subTest(question=question),self.assertRaises(ValueError):
                autonomy.validate_editorial_question(question,source)
        autonomy.validate_editorial_question('Comment suivre le travail des agents ?',source)

    def test_thumbnail_writer_cannot_select_an_anchor_from_a_different_source_unit(self):
        units=[{'index':0,'start':0,'end':10,'text':'Les contrats décrivent les interfaces et leurs règles pour vérifier les changements du produit.'},
               {'index':1,'start':10,'end':20,'text':'Le maquereau est présenté comme un exemple synthétique différent pour isoler les mots autorisés.'}]
        plan={'concepts':[{'concept_index':i,'spoken_unit_index':i%2,'viewer_question':'Quelle question de fixture '+str(i)+' ?'} for i in range(3)]}
        client=ModelDouble(self.config,self.root/'receipts');original=client.complete;seen=[]
        def inspect(role,prompt,data,schema,**kwargs):
            result,proof=original(role,prompt,data,schema,**kwargs)
            if role=='packaging_concept':
                expected=[word for word in autonomy.anchor_words(data['spoken_unit']['text']) if word not in seen]
                self.assertEqual(schema['properties']['anchor_term']['enum'],expected)
                if data['spoken_unit']['index']==0:
                    self.assertNotIn('maquereau',expected)
                    with self.assertRaises(local_models.LocalModelError):
                        local_models.validate({**result,'anchor_term':'maquereau'},schema)
                seen.append(result['anchor_term'])
            return result,proof
        with patch.object(client,'complete',side_effect=inspect):
            response,_=autonomy.design_concepts(client,{'audience':'Fixture','essential_nuance':'Aucun contenu réel.'},units,
                [{'time_seconds':5},{'time_seconds':15}],plan,[],self.config)
        self.assertEqual(len(seen),3)
        for c in response['concepts']:
            self.assertIn(c['anchor_term'],autonomy.anchor_words(units[c['spoken_unit_index']]['text']))

    def test_source_bound_copy_cannot_keep_generated_diagnosis_or_erase_literal_reservation(self):
        quote="Un refus a disparu après un changement de session, mais je ne sais pas pourquoi."
        response={'preferred_index':0,'content_promise':'Diagnostic inventé et garanti.',
            'platform_texts':{'youtube':'Diagnostic inventé'},'concepts':[{'video_title':'Un refus raconté','thumbnail_text':'Changer de session',
                'spoken_unit_index':0,'editorial_question':'Que raconte ce changement de session ?',
                'hypothesis':'Diagnostic inventé','wording_reason':'Garantie inventée','title_image_complementarity':'Diagnostic inventé'}]}
        before=copy.deepcopy(response)
        result=autonomy.source_bound_metadata(response,{'title':'Un changement de session sans explication'},[{'index':0,'text':quote}])
        self.assertEqual(response,before)
        self.assertEqual(result['metadata_mode'],'source_bound_v1')
        self.assertNotIn('inventé',json.dumps(result,ensure_ascii=False))
        self.assertIn(quote,result['platform_texts']['youtube'])
        self.assertEqual(result['concepts'][0]['wording_reason'],'Paroles conservées : "'+quote+'"')
        self.assertEqual(result['concepts'][0]['hypothesis'],'Question éditoriale : Que raconte ce changement de session ?')

    def test_long_literal_quote_is_omitted_whole_instead_of_truncated_in_platform_copy(self):
        quote=('Les données doivent être structurées, avec leurs réserves et leurs conditions. '*30).strip()
        response={'preferred_index':0,'concepts':[{'video_title':'Des données structurées','thumbnail_text':'Garder les conditions',
            'spoken_unit_index':0,'editorial_question':'Comment garder les conditions ?'}]}
        result=autonomy.source_bound_metadata(response,{'title':'Structurer les données'},[{'index':0,'text':quote}])
        self.assertIn(quote,result['concepts'][0]['wording_reason'])
        for platform,text in result['platform_texts'].items():
            self.assertLessEqual(len(text),280 if platform=='x' else 1200)
            self.assertNotIn('Dans cet extrait',text)
            self.assertTrue(text.endswith('discussion SANDBOX.'))

    def test_boundary_refusal_is_preserved_unless_second_reader_explicitly_refutes_it(self):
        class Review:
            verdict='uncertain'
            def complete(self,role,prompt,data,schema,**kwargs):
                if role=='cut_boundaries':return {'start_status':'intact','end_status':'truncated','reason':'Refus à vérifier.'},{'path':'primary'}
                return {'verdict':{'uncertain':'uncertain','confirmed_truncation':'truncated','unsupported_refusal':'intact'}[self.verdict],'reason':'Arbitrage sur les paroles.'},{'path':'second'}
        model=Review();rows=[{'start':0,'end':3,'text':"Je simulerai des pannes et des coupures de réseau."}]
        self.assertFalse(local_quality.cut_boundaries(model,rows,0,3)['passed'])
        model.verdict='confirmed_truncation';self.assertFalse(local_quality.cut_boundaries(model,rows,0,3)['passed'])
        model.verdict='unsupported_refusal';result=local_quality.cut_boundaries(model,rows,0,3)
        self.assertTrue(result['passed']);self.assertEqual(result['end_status'],'truncated')
        self.assertEqual(result['adjudication']['checks'][0]['evidence']['path'],'second')

    def test_acoustic_caption_chunks_preserve_words_punctuation_and_monotonic_bounds(self):
        text='Nous vérifions les mots, puis nous conservons les réserves.'
        tokens=['Nous',' vérifions',' les',' mots',',',' puis',' nous',' conservons',' les',' réserves','.']
        words=[{'word':w,'start':i*.4,'end':(i+1)*.4,'probability':.9} for i,w in enumerate(tokens)]
        source={'start':100,'end':106,'text':text}
        result=local_alignment.word_captions(words,source)
        self.assertEqual(' '.join(r['text'] for r in result),text)
        self.assertTrue(all(100<=r['start']<r['end']<=106 for r in result))
        self.assertTrue(all(a['end']<=b['start'] for a,b in zip(result,result[1:])))
        with self.assertRaisesRegex(ValueError,'changé les mots'):
            local_alignment.word_captions(words,{**source,'text':text+' Garantie.'})
        with self.assertRaisesRegex(ValueError,'Horaires'):
            local_alignment.word_captions([{**w,'start':-1} for w in words],source)

    def test_duplicate_written_concept_is_rejected_before_rendering(self):
        row = {'angle':'Même idée','hypothesis':'Même hypothèse','video_title':'Le même titre','thumbnail_text':'Autre phrase'}
        with self.assertRaisesRegex(ValueError,'recopies un concept précédent'):
            autonomy.validate_local_wording({'concepts':[row]}, self.config, prior_concepts=[row])

    def test_title_evidence_is_read_from_source_index_without_model_rewriting(self):
        rows = [{'text': "On pourrait discuter avec un agent en vocal, puis choisir son trajet."}]
        class Indexed:
            def complete(self, role, prompt, data, schema, **kwargs):
                self.schema = schema
                return {'supported': True, 'evidence_index': 0, 'reason': 'Le passage propose cette possibilité.'}, {'path': 'fixture'}
        model = Indexed()
        result = local_quality.title_support(model, 'Imaginer un agent vocal', rows)
        self.assertEqual(result['quote'], rows[0]['text'])
        self.assertNotIn('quote', model.schema['properties'])
        self.assertEqual(model.schema['properties']['evidence_index']['enum'], [0])

    def test_packaging_citation_keeps_filler_with_following_speech_but_not_across_gap(self):
        units = autonomy.packaging_units([
            {'start': 0, 'end': 2, 'text': 'Moi ce que je remarque.'},
            {'start': 2.1, 'end': 8, 'text': 'Les équipes doivent relire les propositions et conserver les décisions de conception dans leurs règles.'},
            {'start': 20, 'end': 22, 'text': 'Autre sujet.'}])
        self.assertEqual(len(units), 2)
        self.assertTrue(units[0]['text'].startswith('Moi ce que je remarque. Les équipes'))
        self.assertEqual(units[0]['end'], 8)
        self.assertEqual(units[1]['start'], 20)

    def test_relative_clause_stays_with_the_claim_instead_of_the_next_packaging_quote(self):
        first='Nous discutons de la manière dont cet outil effectue ses tests et conserve les résultats pour aider les équipes à examiner les erreurs puis il produit une checklist de tous les bugs.'
        following='Les replays permettent ensuite de revenir sur les étapes du scénario pour comprendre ce qui a été observé pendant cette simulation et regarder le chemin suivi par les utilisateurs dans le produit.'
        units=autonomy.packaging_units([{'start':0,'end':15,'text':first},
            {'start':15.8,'end':17,'text':'que ça a détecté.'},{'start':17.1,'end':34,'text':following}])
        self.assertIn('tous les bugs. que ça a détecté.',units[0]['text'])
        self.assertEqual(' '.join(u['text'] for u in units),first+' que ça a détecté. '+following)

    def test_portrait_crops_preserve_entire_detected_face_at_image_edges(self):
        for face in ([0,0,30,40], [610,320,30,40], [200,100,70,70]):
            x,y,w,h = local_faces.portrait_box(face,640,360)
            self.assertTrue(0 <= x < x+w <= 640 and 0 <= y < y+h <= 360)
            self.assertTrue(x <= face[0] and y <= face[1] and x+w >= face[0]+face[2] and y+h >= face[1]+face[3])
            self.assertEqual(w,h)
        with self.assertRaises(ValueError):local_faces.portrait_box([620,330,60,60],640,360)
        self.assertEqual(local_faces.overlap([0,0,20,20],[30,30,20,20]),0)
        self.assertGreater(local_faces.overlap([0,0,20,20],[1,1,20,20]),.8)

    def test_unusable_portrait_tries_nearby_real_frame_and_keeps_other_failures_blocking(self):
        frames = [{'time_seconds': i*10} for i in range(5)]
        refusal = local_models.LocalModelError('local_thumbnail_face_not_usable')
        with patch.object(autonomy, 'frame_crop', side_effect=[refusal, ([.1,.1,.2,.3], {'scope':'fixture'})]) as crop:
            index, box, proof = autonomy.portrait_frame(None,frames,2)
            self.assertEqual(index,1)
            self.assertEqual(crop.call_count,2)
        with patch.object(autonomy, 'frame_crop', side_effect=refusal) as crop:
            with self.assertRaises(local_models.LocalModelError):autonomy.portrait_frame(None,frames,2)
            self.assertEqual(crop.call_count,3)
        with patch.object(autonomy, 'frame_crop', side_effect=local_models.LocalModelError('local_model_unavailable')) as crop:
            with self.assertRaisesRegex(local_models.LocalModelError,'local_model_unavailable'):autonomy.portrait_frame(None,frames,2)
            self.assertEqual(crop.call_count,1)

    def setUp(self):
        self.config = load_config()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_external_endpoint_and_cloud_models_are_refused(self):
        for address in ("https://example.com", "http://127.0.0.1@evil.example", "http://127.0.0.1:11434/path", "http://127.0.0.1:11434?remote=1"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                local_models.settings({**self.config, "autonomy": {**self.config["autonomy"], "ollama_url": address}})
        self.config["autonomy"]["editorial_model"] = "kimi:cloud"
        with self.assertRaises(ValueError):
            local_models.settings(self.config)

    def test_context_rejection_is_explicit_without_exposing_provider_body(self):
        client = local_models.Ollama(self.config, self.root)
        body = io.BytesIO(b'{"error":"request (28805 tokens) exceeds the available context size (16384 tokens) PRIVATE"}')
        error = HTTPError(client.url+"/api/chat", 400, "Bad request", {}, body)
        with patch.object(client.opener, "open", side_effect=error):
            with self.assertRaisesRegex(local_models.LocalModelError, "^local_model_context_exceeded$") as caught:
                client.request("/api/chat", {"model": "local"})
        self.assertNotIn("PRIVATE", str(caught.exception))

    def test_scoped_inference_reuses_one_model_and_unloads_before_switching(self):
        client = local_models.Ollama(self.config, self.root)
        client.hold_loaded = True
        schema = local_quality.object_schema({"passed": {"type": "boolean"}})
        requests = []
        def request(route, payload):
            requests.append((route, payload))
            return {"message": {"content": '{"passed":true}'}}
        with patch.object(client, "identity", side_effect=lambda model, **_: {"name": model, "sha256": model}), \
             patch.object(client, "request", side_effect=request):
            client.complete("render_review", "review", {"batch": 1}, schema, reviewer=True)
            client.complete("render_review", "review", {"batch": 2}, schema, reviewer=True)
            client.complete("selection", "select", {}, schema)
            client.close()
        self.assertEqual([route for route, _ in requests], ["/api/chat", "/api/chat", "/api/generate", "/api/chat", "/api/generate"])
        self.assertTrue(all(payload["keep_alive"] == 60 for route, payload in requests if route == "/api/chat"))
        self.assertEqual(requests[2][1]["model"], self.config["autonomy"]["review_model"])
        self.assertEqual(requests[-1][1]["keep_alive"], 0)

    def test_provider_output_is_validated_and_attempts_are_bounded(self):
        client = local_models.Ollama(self.config, self.root)
        schema = local_quality.object_schema({"passed": {"type": "boolean"}})
        with patch.object(client, "identity", return_value={"name": "local", "sha256": "a"}), \
             patch.object(client, "request", return_value={"message": {"content": '{"passed":"yes"}'}}) as request:
            with self.assertRaisesRegex(local_models.LocalModelError, "local_model_output_invalid"):
                client.complete("test", "review", {}, schema)
            self.assertEqual(request.call_count, self.config["autonomy"]["maximum_model_attempts"])
            rejected = list((self.root / "rejected").glob("*.json"))
            self.assertEqual(len(rejected), request.call_count)
            self.assertTrue(all(not json.loads(p.read_text())["payload"]["accepted"] for p in rejected))
            self.assertEqual(list(self.root.glob("*.json")), [])
            request.return_value = {"message": {"content": '{"passed":"no"}'}}
            with self.assertRaises(local_models.LocalModelError):
                client.complete("test", "review", {}, schema)
            self.assertEqual(len(list((self.root / "rejected").glob("*.json"))), 2*len(rejected))

    def test_receipt_cache_avoids_repeating_inference_and_rejects_tampering(self):
        client = local_models.Ollama(self.config, self.root)
        schema = local_quality.object_schema({"passed": {"type": "boolean"}})
        with patch.object(client, "identity", return_value={"name": "local", "sha256": "a"}), \
             patch.object(client, "request", return_value={"message": {"content": '{"passed":true}'}}) as request:
            _, proof = client.complete("test", "review", {}, schema)
            client.complete("test", "review", {}, schema)
            self.assertEqual(request.call_count, 1)
            path = Path(proof["path"])
            changed = json.loads(path.read_text())
            changed["payload"]["response"]["passed"] = False
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "modifié"):
                client.complete("test", "review", {}, schema)

    def test_unknown_or_remote_model_is_not_invoked(self):
        client = local_models.Ollama(self.config, self.root)
        with patch.object(client, "request", return_value={"models": []}):
            with self.assertRaisesRegex(local_models.LocalModelError, "not_installed"):
                client.identity("unknown", vision=False)
        responses = [{"models": [{"name": "test", "digest": "a"}]}, {"remote_host": "https://remote", "capabilities": ["vision"]}]
        with patch.object(client, "request", side_effect=responses):
            with self.assertRaisesRegex(local_models.LocalModelError, "cloud_model_refused"):
                client.identity("test", vision=True)

    def test_non_finite_structured_output_is_refused(self):
        with self.assertRaises(local_models.LocalModelError):
            local_models.validate({"score": float("nan")}, local_quality.object_schema({"score": {"type": "number"}}))

    def test_windows_cover_every_cue_without_infinite_overlap(self):
        rows = [{"start": i*4, "end": i*4+4} for i in range(100)]
        indices = list(autonomy.windows(rows, 30))
        self.assertEqual(set().union(*(set(x) for x in indices)), set(range(100)))
        self.assertLess(len(indices), len(rows))

    def test_overlapping_long_windows_can_keep_a_fifteen_minute_subject_whole(self):
        rows = [{"start": i*10, "end": i*10+10} for i in range(360)]
        chunks = list(autonomy.windows(rows, 1200, 900))
        for start in (0, 250, 700, 1100, 1950, 2600):
            self.assertTrue(any(rows[c[0]]["start"] <= start and rows[c[-1]]["end"] >= start+900 for c in chunks))

    def test_boundary_refinement_can_restore_the_question_without_retiming_source(self):
        rows = [{"start": 0, "end": 10, "text": "Quelle différence entre un agent et un bot ?"},
                {"start": 10, "end": 20, "text": "Parce que là on est plus sur un bot."},
                {"start": 20, "end": 30, "text": "La distinction dépend de son autonomie."}]
        proposal = {"start_index": 1, "end_index": 2, "quote_index": 1, "title": "Agents et bots",
                    "context": "Question et réponse.", "essential_nuance": "L'autonomie est discutée."}
        class Refiner:
            invalid = False
            def complete(self, role, prompt, data, schema, *, validator):
                self.data = data
                self.schema = schema
                result = {"start_anchor": "cue-000000", "end_anchor": "cue-000002", "quote_anchor": "cue-000001", "usable": True,
                          "title": "Agents et bots", "reason": "Conserver la question.", "context": "Question puis réponse.",
                          "essential_nuance": "L'autonomie reste discutée."}
                if self.invalid:
                    result["start_anchor"], result["end_anchor"] = "cue-000002", "cue-000001"
                local_models.validate(result, schema)
                validator(result)
                return result, {"test_double": True}
        model = Refiner()
        result, _ = autonomy.refine_boundaries(model, rows, proposal, self.config["autonomy"])
        self.assertEqual(result["start_index"], 0)
        self.assertNotIn("cue-000001", model.schema["properties"]["start_anchor"]["enum"])
        self.assertNotIn("cue-000000", model.schema["properties"]["end_anchor"]["enum"])
        self.assertEqual(model.data["context_before_not_in_cut"][0][-1], rows[0]["text"])
        self.assertEqual(rows[0]["start"], 0)
        self.assertEqual(proposal["start_index"], 1)
        model.invalid = True
        with self.assertRaises(ValueError):
            autonomy.refine_boundaries(model, rows, proposal, self.config["autonomy"])

    def test_truncated_thumbnail_phrases_from_the_real_recipe_are_refused(self):
        examples = [("Les titres et les miniatures doivent ensuite", "Les titres et les miniatures doivent ensuite correspondre aux paroles."),
                    ("Elle permet de vérifier que le master ne", "Elle permet de vérifier que le master ne change pas."),
                    ("Une coupe ne doit pas supprimer une", "Une coupe ne doit pas supprimer une réserve.")]
        for phrase, quote in examples:
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                autonomy.validate_local_wording({"concepts": [{"thumbnail_text": phrase, "video_title": "Une méthode", "spoken_unit_index": 0}]},
                                               self.config, [{"index": 0, "text": quote}])

    def test_concrete_anchor_accepts_punctuation_and_french_plural_without_changing_the_object(self):
        self.assertIn("réserve", autonomy.anchor_words("Préserver une réserve."))
        self.assertTrue(autonomy.anchor_present("réserve", "Réserves : préserver le sens."))
        self.assertTrue(autonomy.anchor_present("master", "Vérifier le master."))
        self.assertFalse(autonomy.anchor_present("master", "Garantir l'authenticité"))

    def test_transcription_cache_binds_source_weights_and_tokenizer_without_network(self):
        directory = self.root / "weights"
        directory.mkdir()
        for name in ("model.bin", "config.json", "tokenizer.json"):
            (directory / name).write_bytes(name.encode())
        self.config["autonomy"]["transcription_model"] = str(directory)
        source = self.root / "master.mp4"
        source.write_bytes(b"source")
        calls = []
        class Recognizer:
            def __init__(self, *args, **kwargs):
                self.assert_offline = kwargs["local_files_only"]
                calls.append(kwargs)
            def transcribe(self, *args, **kwargs):
                self.transcription_options = kwargs
                return iter([SimpleNamespace(start=0, end=12, text="Une explication complète.", words=[], no_speech_prob=.95)]), SimpleNamespace(language="fr")
        with patch.dict(sys.modules, {"faster_whisper": SimpleNamespace(WhisperModel=Recognizer),
                                     "huggingface_hub": SimpleNamespace(hf_hub_download=lambda *_a, **_k: self.fail("Pas de téléchargement"))}):
            transcript, _ = local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(transcript["segments"]), 1)
            self.assertEqual(transcript["segments"][0]["no_speech_probability"], .95)
            local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(calls), 1)
            (directory / "tokenizer.json").write_bytes(b"new tokenizer")
            local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(calls), 2)
            source.write_bytes(b"changed source")
            local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(calls), 3)
            (directory / "preprocessor_config.json").write_bytes(b"different mel settings")
            local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(calls), 4)
            self.config["autonomy"]["transcription_model"] = "dropbox-dash/faster-whisper-large-v3-turbo"
            def cached_file(repository, filename, *, local_files_only):
                self.assertEqual(repository, "dropbox-dash/faster-whisper-large-v3-turbo")
                self.assertTrue(local_files_only)
                return str(directory / filename)
            with patch.dict(sys.modules, {"huggingface_hub": SimpleNamespace(hf_hub_download=cached_file)}):
                local_models.transcribe(source, self.root / "cache", self.config)
            self.assertEqual(len(calls), 4)
            self.assertTrue(all(c["local_files_only"] for c in calls))


class AudioQualityTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1", "Recette média réelle requise.")
    def test_headroom_repair_preserves_encoded_pictures_source_and_audio_alignment(self):
        from youtube_growth.factory import media
        from youtube_growth.shorts import _require_media_tools
        ffmpeg, _ = _require_media_tools()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);source = root / "source.mp4"
            subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-n", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=7",
                "-f", "lavfi", "-i", "aevalsrc=0.1*sin(2*PI*(180*t+23*t*t)):s=22050:d=7",
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(source)], check=True)
            original = fingerprint(source)
            asset = media.render(source, {"start_seconds": .65, "end_seconds": 5.65}, root / "renders", format="horizontal", fixture=True)
            revised = local_audio.repair_headroom(asset)
            self.assertEqual(fingerprint(source), original)
            self.assertEqual(fingerprint(Path(asset["path"])), asset["sha256"])
            def packets(path):
                return subprocess.check_output([ffmpeg, "-nostdin", "-v", "error", "-i", str(path), "-map", "0:v:0",
                    "-c:v", "copy", "-f", "hash", "-hash", "sha256", "-"])
            self.assertEqual(packets(asset["path"]), packets(revised["path"]))
            self.assertTrue(local_quality.audio_correspondence(source, revised)["passed"])
            self.assertLess(revised["qa"]["details"]["max_volume_db"], asset["qa"]["details"]["max_volume_db"])
            self.assertEqual(local_audio.repair_headroom(asset)["asset_id"], revised["asset_id"])
            with self.assertRaises(ValueError):local_audio.repair_headroom(revised)

    def test_gain_is_accepted_but_shifted_replaced_and_silent_sound_are_rejected(self):
        import numpy as np
        sound = np.random.default_rng(42).normal(size=200_000).astype("<f4")
        other = np.random.default_rng(17).normal(size=200_000).astype("<f4")
        source, video = Path("source.mp4"), Path("video.mp4")
        asset = {"path": str(video), "cuts": [{"source_start_seconds": 10, "source_end_seconds": 20,
                                                "output_start_seconds": 0, "output_end_seconds": 10}]}
        def exercise(shift=0, replacement=False, silence=False):
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            def decode(path, directory):
                signal = other if path == video and replacement else sound
                result = signal[round((10+shift)*4000):] if path == video else signal
                if silence:
                    result = np.zeros_like(result)
                elif path == video:
                    result = result*2
                target = Path(temporary.name) / (path.name+".pcm")
                target.write_bytes(result.astype("<f4").tobytes())
                return target
            with patch.object(local_quality, "pcm_audio", side_effect=decode):
                return local_quality.audio_correspondence(source, asset)
        self.assertTrue(exercise()["passed"])
        self.assertFalse(exercise(shift=.12)["passed"])
        self.assertFalse(exercise(replacement=True)["passed"])
        self.assertFalse(exercise(silence=True)["passed"])

    @unittest.skipUnless(os.environ.get('FACTORY_MEDIA_INTEGRATION') == '1', 'Activer la recette AAC flottante.')
    def test_aac_peak_above_zero_requires_measured_gain_and_preserves_original(self):
        from youtube_growth.factory import media
        from youtube_growth.shorts import _require_media_tools
        ffmpeg, _ = _require_media_tools()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); directory=root/'input'; directory.mkdir(); source=directory/'video.mp4'
            subprocess.run([ffmpeg,'-nostdin','-v','error','-n','-f','lavfi','-i','testsrc2=size=320x180:rate=25:duration=3',
                '-f','lavfi','-i','aevalsrc=1.8*sin(2*PI*710*t):s=48000:d=3','-c:v','libx264','-preset','ultrafast',
                '-c:a','aac','-shortest',str(source)],check=True)
            srt=directory/'subtitles.srt';srt.write_text('1\n00:00:00,000 --> 00:00:03,000\nFixture audio uniquement.\n',encoding='utf-8')
            ass=directory/'subtitles.ass';ass.write_text('[Script Info]\n',encoding='utf-8')
            sha=fingerprint(source); details=media._scan(source)
            self.assertEqual(details['max_volume_db'],0)
            self.assertGreater(local_audio.decoded_peak(source),1.5)
            asset={'asset_id':'float-aac-fixture','path':str(source),'master_path':str(source),'sha256':sha,'master_sha256':sha,
                'source_sha256':sha,'subtitle_path':str(srt),'subtitle_sha256':fingerprint(srt),'ass_path':str(ass),
                'ass_sha256':fingerprint(ass),'duration_seconds':media.probe(source)['duration_seconds'],'width':320,'height':180,
                'qa':{'technical':'needs_review','details':details},'parameters':{}}
            repaired=local_audio.repair_headroom(asset)
            self.assertLess(repaired['audio_headroom']['gain_db'],-3)
            self.assertLess(local_audio.decoded_peak(Path(repaired['path'])),-.1)
            self.assertEqual(repaired['qa']['technical'],'passed')
            self.assertEqual(fingerprint(source),sha)
            with self.assertRaises(ValueError):local_audio.repair_headroom(repaired)

    @unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1", "Activer la recette média pour vérifier l'amorce AAC.")
    def test_aac_priming_does_not_shift_rendered_audio_at_zero_or_nonzero_cut(self):
        from youtube_growth.factory import media
        from youtube_growth.shorts import _require_media_tools
        ffmpeg, _ = _require_media_tools()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-n", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=7",
                "-f", "lavfi", "-i", "aevalsrc=0.1*sin(2*PI*(180*t+23*t*t)):s=22050:d=7",
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(source)], check=True)
            for start in (0, .65):
                asset = media.render(source, {"start_seconds": start, "end_seconds": start+5}, root / "renders", format="horizontal", fixture=True)
                quality = local_quality.audio_correspondence(source, asset)
                self.assertTrue(quality["passed"], quality)


class OrthographyTests(unittest.TestCase):
    def test_sparse_candidates_are_reviewed_together_without_changing_other_units(self):
        raw = {"segments": [{"start": i, "end": i+1, "text": "Bonjour."} for i in range(1000)]}
        for i in (20, 400, 900):
            raw["segments"][i]["text"] = "Les source fiables."
        class Reader:
            calls = []
            def complete(self, role, prompt, data, schema, **kwargs):
                self.calls.append(data)
                return {"edits": []}, {"role": role}
        reader = Reader()
        result = proofread(raw, reader)
        self.assertEqual(len(reader.calls), 1)
        self.assertEqual(result["orthography"]["candidate_unit_indices"], [20, 400, 900])
        self.assertEqual([u["index"] for u in reader.calls[0]["units"]], [20, 400, 900])
        self.assertEqual(result["segments"], raw["segments"])

    def test_split_real_master_sentence_cannot_be_completed_or_merged(self):
        raw = {"segments": [{"start": 3.16, "end": 8, "text": "personne n'a pensé à les"},
                            {"start": 8, "end": 9, "text": "arrêter."},
                            {"start": 9, "end": 11, "text": "Les source fiables."}]}
        class Writer:
            def complete(self, role, prompt, data, schema, **kwargs):
                if role == "transcript_orthography_tokens":
                    # The schema contains only single-word operations. The
                    # actual rejected model completion cannot match it.
                    with self_test.assertRaises(local_models.LocalModelError):
                        local_models.validate({"edits": [{"index": 0, "corrected": "personne n'a pensé à les arrêter.",
                                                          "reason": "compléter la phrase"}]}, schema)
                    return {"edits": []}, {"role": role}
                raise AssertionError("No edit needs no independent correction review")
        self_test = self
        result = proofread(raw, Writer())
        self.assertEqual(result["segments"], raw["segments"])
        self.assertEqual(result["orthography"]["changes"], [])

    def test_surface_guard_accepts_agreements_but_refuses_changed_words_numbers_and_negation(self):
        self.assertTrue(same_spoken_words("au parole réellement conservée", "aux paroles réellement conservées"))
        for before, after in [("Il ne faut pas publier", "Il faut publier"), ("Deux vidéos", "Trois vidéos"),
                              ("Un modèle local", "Un modèle distant"), ("Les sources", "Le source"),
                              ("C'est prêt ?", "C'est prêt.")]:
            self.assertFalse(same_spoken_words(before, after), (before, after))

    def test_correction_preserves_raw_asr_and_timestamps_and_requires_distinct_review(self):
        raw = {"segments": [{"start": 0, "end": 5, "text": "au parole réellement conservée"}]}
        class Reviewer:
            approved = True
            def complete(self, role, prompt, data, schema, **kwargs):
                if role == "transcript_orthography_tokens":
                    return {"edits": [{"index": 0, "word_index": i, "replacement": value}
                                      for i, value in ((0, "aux"), (1, "paroles"), (3, "conservées"))]}, {"role": role}
                return {"approved": self.approved, "reason": "Accords orthographiques uniquement."}, {"role": role}
        model = Reviewer()
        result = proofread(raw, model)
        self.assertEqual(raw["segments"][0]["text"], "au parole réellement conservée")
        self.assertEqual(result["segments"][0]["text"], "aux paroles réellement conservées")
        self.assertEqual(result["segments"][0]["start"], 0)
        self.assertEqual(result["segments"][0]["end"], 5)
        self.assertEqual(len(result["orthography"]["receipts"]), 2)
        model.approved = False
        refused = proofread(raw, model)
        self.assertEqual(refused["segments"], raw["segments"])
        self.assertFalse(refused["orthography"]["changes"])
        self.assertEqual(len(refused["orthography"]["rejected_corrections"]), 1)


if __name__ == "__main__":
    unittest.main()
