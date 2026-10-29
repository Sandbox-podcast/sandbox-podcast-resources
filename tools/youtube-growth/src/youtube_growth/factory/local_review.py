"""Explicit independent thumbnail review; no audio attestation or social action."""
from __future__ import annotations

from pathlib import Path

from .contracts import digest, load_json, iso, utcnow
from .local_models import validate, LocalModelError
from .local_quality import TEXT, object_schema, verify_evidence_files
from .media import fingerprint
from .thumbnails import CHECKS, validate_bundle, review_bundle


def assert_review(bundle: dict, asset: dict) -> None:
    validate_bundle(bundle, asset=asset, require_review=True)
    proof=bundle.get('independent_local_review',{})
    if (proof.get('content_digest')!=bundle['content_digest'] or proof.get('asset_sha256')!=asset['sha256']
            or proof.get('editorial_revision')!=asset.get('local_editorial_revision')
            or proof.get('scope')!='independent_agent_images_and_text' or proof.get('human_listening') is not False):
        raise LocalModelError('local_independent_review_changed')
    verify_evidence_files(proof)


def adopt_packaging(store, config: dict, bundle_id: str, report_path: Path, *, now=None) -> dict:
    from .analytics import ensure_packaging_unlocked
    from .autonomy import (_directory, _segments, assert_local_asset, packaging_units, source_bound_metadata,
                           validate_editorial_question, punctuation, write_json, supersede_bundles, run_key, PACKAGING_VERSION)
    from .local_exports import export_pack
    from .packaging import revision
    bundle=store.get('thumbnail_bundle',bundle_id)
    if not bundle:raise ValueError('Bundle local inconnu.')
    episode=store.get('episode',bundle['episode_id'])
    if fingerprint(Path(episode['source']))!=episode['source_sha256']:
        raise LocalModelError('local_independent_review_source_changed')
    asset=next((a for a in store.records('asset',episode['episode_id'])
        if a['segment_id']==bundle['segment_id'] and a['sha256']==bundle['asset_sha256'] and a.get('qa_status')!='superseded'),None)
    if not asset:raise ValueError('Montage courant requis.')
    assert_local_asset(episode,asset);validate_bundle(bundle,asset=asset)
    candidate=store.get('candidate',asset['segment_id'])
    if (candidate.get('decision')!='retained' or candidate.get('local_run_key')!=run_key(episode,config)
            or asset.get('local_run_key')!=candidate.get('local_run_key')):raise ValueError('Passage courant retenu requis.')
    report_path=report_path.resolve(strict=True);report=load_json(report_path)
    if not isinstance(report.get('bundles'),list):raise ValueError('Rapport indépendant structuré requis.')
    row=next((r for r in report['bundles'] if r.get('bundle_id')==bundle_id),None)
    if not row:raise ValueError('Ce bundle est absent du rapport.')
    fields={'bundle_id':{'const':bundle_id},'content_digest':{'const':bundle['content_digest']},'status':{'const':'passed'},
        'source_sha256':{'const':bundle['source_sha256']},'asset_sha256':{'const':asset['sha256']},
        'scope':{'const':'images_and_text_only'},'human_listening':{'const':False},
        'checks':object_schema({name:{'const':True} for name in sorted(CHECKS)}),
        'blocking_findings':{'type':'array','maxItems':0},
        'opened_files':{'type':'array','minItems':10,'maxItems':1000,'items':TEXT}}
    selected=validate({'reviewer':report.get('reviewer'),'row':{k:row.get(k) for k in fields}},
        object_schema({'reviewer':TEXT,'row':object_schema(fields)}))
    expected={Path(a['path']).resolve() for a in bundle['artifacts'] if a['kind'] in {'thumbnail','preview_320','preview_160','comparison'}}
    if len(expected)!=10 or not expected<={Path(p).resolve() for p in row['opened_files']}:
        raise ValueError('Inspection explicite des dix images courantes requise.')
    brief=load_json(Path(bundle['brief_path']))
    if (brief.get('metadata_mode')!='source_bound_v1' or punctuation(brief['essential_nuance'])!=punctuation(candidate['essential_nuance'])):
        raise ValueError('Brief courant lié aux paroles requis.')
    units=[]
    for cut in asset['cuts']:
        kept=[r for r in _segments(episode) if cut['source_start_seconds']<=r['start'] and r['end']<=cut['source_end_seconds']]
        for unit in packaging_units(kept):units.append({'index':len(units),**unit})
    for concept in brief['concepts']:
        unit=next(u for u in units if u['index']==concept['spoken_unit_index'])
        validate_editorial_question(concept['editorial_question'],unit['text'])
        proofs=[p for p in brief['content_evidence'] if p['evidence_id'] in concept['evidence_ids']]
        if not proofs or any(p['quote']!=unit['text'] or punctuation(p['context'])!=punctuation(candidate['context']) for p in proofs):
            raise ValueError('Citation ou contexte différent des paroles courantes.')
    index=next(i for i,c in enumerate(brief['concepts']) if c['concept_id']==bundle['selected_concept_id'])
    response=source_bound_metadata({'concepts':brief['concepts'],'preferred_index':index},candidate,units)
    for field in ('viewer_question','content_promise','selection_reason'):
        if punctuation(response[field])!=punctuation(brief[field]):raise ValueError('Métadonnée non liée à la source : '+field)
    reference={'path':str(report_path),'sha256':fingerprint(report_path)}
    if (bundle.get('independent_local_review',{}).get('report')==reference
            and bundle.get('review_status')=='passed'):
        assert_review(bundle,asset)
        return {'bundle_id':bundle_id,'status':'already_adopted','human_listening':False}
    binding={'report':reference,'bundle_id':bundle_id,'content_digest':bundle['content_digest'],'asset_sha256':asset['sha256'],
        'source_sha256':episode['source_sha256'],'editorial_revision':asset.get('local_editorial_revision'),
        'reviewer':selected['reviewer'],'checks':row['checks'],'scope':'independent_agent_images_and_text',
        'human_listening':False,'reviewed_at':iso(now or utcnow())}
    receipt=_directory(store,episode)/'independent-reviews'/(digest(binding)+'.json');write_json(receipt,binding)
    reviewed=review_bundle(bundle,reviewer=selected['reviewer'],evidence=str(receipt),checks=sorted(CHECKS),now=now)
    reviewed['independent_local_review']={**binding,'path':str(receipt),'sha256':fingerprint(receipt)}
    assert_review(reviewed,asset)
    chosen=reviewed['variants'][index]
    with store.transaction():
        if any(j['status']=='running' and j['payload'].get('asset_id')==asset['asset_id'] for j in store.jobs()):
            raise ValueError('Attendre la fin du traitement de ce média.')
        all_packs=[p for p in store.publications(episode['episode_id']) if p['asset_id']==asset['asset_id']]
        if any(not p.get('local_only') or p.get('remote_id') or p.get('scheduled_at') for p in all_packs):
            raise ValueError('Une intention distante interdit cette revue locale.')
        packs=[p for p in all_packs if p['status'] not in {'archived','cancelled'}]
        if not packs:raise ValueError('Packs locaux courants requis.')
        for pack in packs:ensure_packaging_unlocked(pack['id'],store.records('experiment'))
        for job in store.jobs():
            if job['kind']=='local_thumbnails' and job['payload'].get('asset_id')==asset['asset_id'] and job['status'] in {'queued','blocked','failed'}:
                store.db.execute("UPDATE jobs SET status='cancelled',last_error='replaced_by_independent_review' WHERE id=?",(job['id'],))
        supersede_bundles(store,asset,bundle_id,now=now)
        store.put('thumbnail_bundle',bundle_id,reviewed,episode_id=episode['episode_id'],now=now)
        for pack in packs:
            pack.update(title=chosen['title'],text=punctuation(response['platform_texts'][pack['platform']]),
                cover=chosen['thumbnail']['path'],cover_sha256=chosen['thumbnail']['sha256'],thumbnail_bundle=reviewed,
                variants=reviewed['variants'],local_only=True,status='local_ready',qa_status='local_passed',
                packaging_status='independent_passed',scheduled_at=None,blocked_reason=None,local_packaging_version=PACKAGING_VERSION)
            pack['local_packaging_review']={'revision':revision(pack),'bundle_digest':reviewed['content_digest'],
                'scope':'independent_agent_images_and_text','human_review':False,'evidence':reviewed['independent_local_review']}
            pack=export_pack(pack,asset,episode,_directory(store,episode)/'packs')
            store.save_publication(pack,now=now);store.put('packaging',pack['id'],pack,episode_id=episode['episode_id'],now=now)
        store.event('local_independent_packaging_review_adopted',asset['asset_id'],
            {'bundle_id':bundle_id,'evidence':reviewed['independent_local_review'],'previous_model_passed':bundle.get('local_review',{}).get('passed')},now=now)
    return {'bundle_id':bundle_id,'packs':len(packs),'status':'independent_passed','human_listening':False}
