"""Persistent master-to-calendar preparation. No publication jobs or social I/O."""
from __future__ import annotations

from datetime import timedelta
import copy
import json
import os
import re
from pathlib import Path
import tempfile

from .contracts import ROOT, PARIS, digest, instant, iso, load_json, utcnow
from .local_models import LocalModelError, Ollama, settings, transcribe
from .local_quality import TEXT, audio_correspondence, object_schema, review_images, samples, technical_checks, title_support, cut_boundaries, verify_review_files, verify_evidence_files
from .media import fingerprint
from .efficiency import measured
from ..thematic_core import read_transcript, sentences

KINDS = {"local_transcribe", "local_analyze", "local_recheck", "local_render", "local_quality", "local_thumbnails", "local_calendar"}
PACKAGING_VERSION = 5
QUALITY_VERSION = 2
RENDER_PROFILE = 'local_caption_band_v1'


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def run_key(episode: dict, config: dict) -> str:
    from .media import RENDERER_VERSION
    return digest({"version": 4, "renderer": RENDERER_VERSION, "revision": episode["revision"], "configuration": settings(config)})


def payload(episode: dict, config: dict, **values) -> dict:
    return {"revision": episode["revision"], "local_run_key": run_key(episode, config), **values}


def artifact_signatures(store, episode: dict, key: str) -> list:
    """Cheap change detection; the calendar then verifies the recorded byte hashes."""
    paths = {episode["source"]}
    if episode.get("transcript"):
        paths.add(episode["transcript"])
    def references(value):
        if isinstance(value, dict):
            for name, child in value.items():
                if name in {"path", "brief_path", "receipt_path", "subtitle_path", "ass_path", "master_path"} and isinstance(child, str):
                    paths.add(child)
                elif isinstance(child, (dict, list)):
                    references(child)
        elif isinstance(value, list):
            for child in value:
                references(child)
    for kind in ("asset", "candidate", "thumbnail_bundle"):
        for record in store.records(kind, episode["episode_id"]):
            if record.get("local_run_key") == key or kind == "thumbnail_bundle":
                references(record)
                if kind == "thumbnail_bundle":
                    brief_path = Path(record["brief_path"])
                    try:
                        brief = load_json(brief_path) if brief_path.stat().st_size <= 8_000_000 else {}
                    except (OSError, ValueError):
                        # The brief itself is already tracked and will fail the
                        # calendar's byte/structure verification.
                        brief = {}
                    if isinstance(brief, dict):
                        for field in ("generation_evidence", "concept_plan", "citation_alignment"):
                            references(brief.get(field, {}))
    result = []
    for value in sorted(paths):
        try:
            stat = Path(value).stat()
            result.append([value, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns])
        except OSError:
            result.append([value, None])
    return result


def advance(store, config: dict, *, now=None) -> None:
    """Recover transitions even if a process dies after committing a stage."""
    if not settings(config).get("enabled"):
        return
    for episode in store.records("episode"):
        if episode.get("local_autonomy") is not True:
            continue
        key = run_key(episode, config)
        with store.transaction():
            run = store.get("local_run", key)
            if run is None:
                old_calendar = store.get("local_calendar", episode["episode_id"])
                if old_calendar and old_calendar.get("local_run_key") != key:
                    old_calendar.update(status="superseded", previous_planned=old_calendar.get("planned", []), planned=[])
                    store.put("local_calendar", episode["episode_id"], old_calendar, episode_id=episode["episode_id"], now=now)
                run = {"local_run_key": key, "episode_id": episode["episode_id"], "revision": episode["revision"],
                       "status": "queued", "created_at": iso(now or utcnow()), "local_only": True}
                store.put("local_run", key, run, episode_id=episode["episode_id"], now=now)
                store.enqueue("local_transcribe", episode["episode_id"], payload(episode, config), now=now)
            jobs = [j for j in store.jobs() if j["payload"].get("local_run_key") == key]
            active_pairs={(a['segment_id'],a['sha256']) for a in store.records('asset',episode['episode_id']) if a.get('qa_status')!='superseded'}
            for bundle in store.records('thumbnail_bundle',episode['episode_id']):
                if (bundle['segment_id'],bundle['asset_sha256']) not in active_pairs and bundle.get('review_status')!='superseded':
                    bundle.update(previous_review_status=bundle['review_status'],review_status='superseded',replacement_bundle_id=None)
                    store.put('thumbnail_bundle',bundle['bundle_id'],bundle,episode_id=episode['episode_id'],now=now)
            for job in jobs:
                if (job["kind"] == "local_thumbnails" and (job["payload"].get("packaging_version") != PACKAGING_VERSION or job['payload'].get('quality_version') != QUALITY_VERSION)
                        and job["status"] in {"queued", "blocked", "failed"}):
                    store.db.execute("UPDATE jobs SET status='cancelled',last_error='superseded_by_packaging_version' WHERE id=?", (job["id"],))
                if job['kind']=='local_render' and job['payload'].get('render_profile') != RENDER_PROFILE and job['status'] in {'queued','blocked','failed'}:
                    store.db.execute("UPDATE jobs SET status='cancelled',last_error='superseded_by_render_profile' WHERE id=?",(job['id'],))
            for asset in store.records("asset"):
                if asset.get("local_run_key") != key or asset.get("qa_status") == 'superseded':
                    continue
                candidate = store.get("candidate", asset["segment_id"])
                if candidate.get("decision") != "retained":
                    continue
                if asset.get('parameters',{}).get('layout') != 'fit_preserve_all_pixels_local_captions_v1':
                    from .analytics import ensure_packaging_unlocked
                    for pack in store.publications(episode['episode_id']):
                        if pack['asset_id'] != asset['asset_id']:continue
                        if not pack.get('local_only') or pack.get('remote_id') or pack.get('scheduled_at'):
                            raise LocalModelError('local_render_profile_remote_intent_refused')
                        ensure_packaging_unlocked(pack['id'],store.records('experiment'))
                        pack.update(status='archived',qa_status='superseded',scheduled_at=None)
                        store.save_publication(pack,now=now)
                    asset.update(qa_status='superseded')
                    store.put('asset',asset['asset_id'],asset,episode_id=episode['episode_id'],now=now)
                    supersede_bundles(store,asset,now=now)
                    calendar=store.get('local_calendar',episode['episode_id'])
                    if calendar and calendar.get('planned'):
                        calendar.update(status='running',previous_planned=calendar['planned'],planned=[],valid_for_publication=False)
                        store.put('local_calendar',episode['episode_id'],calendar,episode_id=episode['episode_id'],now=now)
                    for obsolete in store.jobs():
                        if obsolete['payload'].get('asset_id')==asset['asset_id'] and obsolete['status'] in {'queued','blocked','failed'}:
                            store.db.execute("UPDATE jobs SET status='cancelled',last_error='superseded_by_render_profile' WHERE id=?",(obsolete['id'],))
                    continue
                if asset.get('qa_status') != 'local_passed':continue
                if asset.get('local_quality_version') != QUALITY_VERSION:
                    asset.update(qa_status='needs_review')
                    store.put('asset',asset['asset_id'],asset,episode_id=episode['episode_id'],now=now)
                    args={'asset_id':asset['asset_id'],'quality_version':QUALITY_VERSION}
                    if candidate.get('local_editorial_revision'):args['editorial_revision']=candidate['local_editorial_revision']
                    store.enqueue('local_quality',episode['episode_id'],payload(episode,config,**args),now=now)
                    calendar = store.get('local_calendar',episode['episode_id'])
                    if calendar and calendar.get('planned'):
                        calendar.update(status='running',previous_planned=calendar['planned'],planned=[],valid_for_publication=False)
                        store.put('local_calendar',episode['episode_id'],calendar,episode_id=episode['episode_id'],now=now)
                    continue
                packs = [p for p in store.publications(episode["episode_id"]) if p["asset_id"] == asset["asset_id"] and p.get("status") not in {"archived", "cancelled"}]
                for pack in packs:
                    if pack.get("status") == "local_ready" and pack.get("local_packaging_version") == PACKAGING_VERSION and pack.get("local_export_version") != 1:
                        from .local_exports import export_pack
                        exported = export_pack(pack, asset, episode, _directory(store,episode) / "packs")
                        store.save_publication(exported, now=now)
                if packs and any(p.get("local_packaging_version") != PACKAGING_VERSION for p in packs):
                    supersede_bundles(store, asset, now=now)
                    for pack in packs:
                        pack.update(status="local_preparing", packaging_status="needs_review", scheduled_at=None)
                        store.save_publication(pack, now=now)
                    args = {"asset_id": asset["asset_id"], "packaging_version": PACKAGING_VERSION, 'quality_version':QUALITY_VERSION}
                    if candidate.get("local_editorial_revision"):args["editorial_revision"] = candidate["local_editorial_revision"]
                    store.enqueue("local_thumbnails", episode["episode_id"], payload(episode, config, **args), now=now)
                    calendar = store.get("local_calendar", episode["episode_id"])
                    if calendar and calendar.get("planned"):
                        calendar.update(status="running", previous_planned=calendar["planned"], planned=[], valid_for_publication=False)
                        store.put("local_calendar", episode["episode_id"], calendar, episode_id=episode["episode_id"], now=now)
            for candidate in store.records('candidate',episode['episode_id']):
                if candidate.get('local_run_key') != key or candidate.get('decision') != 'retained':continue
                current_assets=[a for a in store.records('asset',episode['episode_id']) if a['segment_id']==candidate['segment_id'] and a.get('qa_status')!='superseded'
                                and a.get('parameters',{}).get('layout')=='fit_preserve_all_pixels_local_captions_v1']
                if not current_assets:
                    args={'segment_id':candidate['segment_id'],'render_profile':RENDER_PROFILE}
                    if candidate.get('local_editorial_revision'):args['editorial_revision']=candidate['local_editorial_revision']
                    store.enqueue('local_render',episode['episode_id'],payload(episode,config,**args),now=now)
            jobs = [j for j in store.jobs() if j["payload"].get("local_run_key") == key]
            active = any(j["status"] in {"queued", "running"} for j in jobs)
            stages = [{"id": j["id"], "status": j["status"]} for j in jobs if j["kind"] != "local_calendar"]
            if stages and not active:
                local_now = instant(now or utcnow()).astimezone(PARIS)
                clock = [local_now.date().isoformat(), sum(t <= local_now.strftime("%H:%M") for t in config["schedule"]["slots_local"])]
                stamp = digest({"stages": stages, "clock": clock, "files": artifact_signatures(store, episode, key),
                                "packs": [p for p in store.publications(episode["episode_id"]) if p.get("local_run_key") == key]})
                store.enqueue("local_calendar", episode["episode_id"], payload(episode, config, calendar_revision=stamp), now=now)


def prepare_master(store, config: dict, source: Path, *, episode_id: str, title: str,
                   publication_at=None, next_filming_at=None, transcript: Path | None = None,
                   full_episode_url=None, full_episode_id=None, synthetic=False, now=None) -> dict:
    from .runtime import ingest
    if not settings(config).get("enabled"):
        raise LocalModelError("local_autonomy_disabled")
    source = source.resolve(strict=True)
    before = source.stat()
    source_hash = fingerprint(source)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Le master a changé pendant sa préparation.")
    manifest = {"version": 1, "episode_id": episode_id, "title": title, "source": str(source),
                "source_sha256": source_hash, "timezone": "Europe/Paris", "availability": "unknown",
                "local_autonomy": True, "synthetic": synthetic}
    for name, value in (("planned_publication_at", publication_at), ("next_filming_at", next_filming_at),
                        ("full_episode_url", full_episode_url), ("full_episode_id", full_episode_id)):
        if value:
            manifest[name] = value
    if transcript:
        manifest["transcript"] = str(transcript.resolve(strict=True))
    # Validate IDs before constructing a path from them.
    from .contracts import validate_episode
    validate_episode(manifest)
    path = store.directory / "inbox" / (episode_id+".ready.json")
    write_json(path, manifest)
    result = ingest(store, path, now=now, verify_source=True)
    advance(store, config, now=now)
    return result


def _episode(store, job: dict, config: dict) -> dict | None:
    episode = store.get("episode", job["episode_id"])
    if not episode or episode.get("local_autonomy") is not True or payload(episode, config)["local_run_key"] != job["payload"]["local_run_key"]:
        return None
    if fingerprint(Path(episode["source"])) != episode["source_sha256"]:
        raise LocalModelError("local_master_changed")
    return episode


def _directory(store, episode: dict) -> Path:
    return store.directory / "episodes" / episode["episode_id"] / "autonomy" / episode["source_sha256"][:24]


def invalidate_calendar(store, job: dict, reason: str, *, now=None) -> None:
    if reason not in {"local_master_changed", "local_transcript_changed"}:
        return
    calendar = store.get("local_calendar", job["episode_id"])
    if calendar and calendar.get("local_run_key") == job["payload"].get("local_run_key"):
        calendar.update(status="blocked", stale=True, generated_at=iso(now or utcnow()),
                        previous_planned=calendar.get("planned", []), planned=[], ready_packs=0,
                        blocked=[{"reason": reason}], valid_for_publication=False)
        path = store.directory / "reports" / (job["episode_id"]+"-invalidated-"+digest(calendar)[:24]+".json")
        calendar["report_path"] = str(path)
        write_json(path, calendar)
        store.put("local_calendar", job["episode_id"], calendar, episode_id=job["episode_id"], now=now)
        run = store.get("local_run", job["payload"]["local_run_key"])
        store.put("local_run", job["payload"]["local_run_key"], {**run, "status": "blocked", "reason": reason}, episode_id=job["episode_id"], now=now)


def _model(store, episode: dict, config: dict) -> Ollama:
    if getattr(store, "_local_inference_scope", False):
        client = getattr(store, "_local_inference_client", None)
        if client is None:
            client = Ollama(config, _directory(store, episode) / "model-receipts")
            client.hold_loaded = True
            store._local_inference_client = client
        return client
    return Ollama(config, _directory(store, episode) / "model-receipts")


def _segments(episode: dict) -> list[dict]:
    return read_transcript(Path(episode["transcript"]), episode["source_probe"]["duration_seconds"], source_hash=episode["source_sha256"])


def transcription(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    directory = _directory(store, episode)
    if episode.get("transcript") and not episode.get("local_generated_transcript"):
        segments = _segments(episode)
        proof = {"path": episode["transcript"], "sha256": fingerprint(Path(episode["transcript"])), "kind": "supplied_transcript"}
    else:
        result, proof = transcribe(Path(episode["source"]), directory / "transcription-cache", config)
        from .local_transcript import proofread
        result = proofread(result, _model(store, episode, config))
        target = directory / ("transcript-"+digest({"model": proof["model"], "result": result})+".json")
        write_json(target, result)
        episode.update(transcript=str(target), local_generated_transcript=True)
        segments = _segments(episode)
    episode["transcript_sha256"] = fingerprint(Path(episode["transcript"]))
    with store.transaction():
        store.put("episode", episode["episode_id"], episode, episode_id=episode["episode_id"], now=now)
        store.put("local_transcription", job["payload"]["local_run_key"], {"episode_id": episode["episode_id"], "proof": proof,
                  "segments": len(segments), "transcript_sha256": episode["transcript_sha256"]}, episode_id=episode["episode_id"], now=now)
        store.enqueue("local_analyze", episode["episode_id"], payload(episode, config), now=now)
    return {"segments": len(segments), "proof": proof}


def windows(segments: list[dict], seconds: int, overlap_seconds=0):
    start = 0
    while start < len(segments):
        end = start+1
        while end < len(segments) and segments[end]["end"]-segments[start]["start"] <= seconds:
            end += 1
        yield list(range(start, end))
        if end == len(segments):
            break
        if overlap_seconds:
            threshold = segments[end-1]["end"]-min(overlap_seconds, seconds-1)
            following = next((i for i in range(start+1, end) if segments[i]["start"] >= threshold), end-1)
            start = max(start+1, following)
        else:
            start = max(start+1, end-1)


CANDIDATE_SCHEMA = object_schema({"start_index": {"type": "integer", "minimum": 0},
    "end_index": {"type": "integer", "minimum": 0}, "quote_index": {"type": "integer", "minimum": 0},
    "title": {"type": "string", "minLength": 1, "maxLength": 110}, "audience": TEXT, "rationale": TEXT,
    "context": TEXT, "essential_nuance": TEXT, "format": {"enum": ["vertical", "horizontal"]},
    "platforms": {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"enum": ["youtube", "instagram", "tiktok", "x", "linkedin"]}},
    "risks": {"type": "array", "items": TEXT, "maxItems": 20}})
ANALYSIS_SCHEMA = object_schema({"summary": TEXT, "candidates": {"type": "array", "items": CANDIDATE_SCHEMA, "maxItems": 100}})


def orphaned_start(text: str) -> bool:
    words = re.findall(r"[^\W_]+", text.casefold())
    return words[:2] == ["parce", "que"] or (len(words) <= 4 and words[:2] == ["ou", "alors"])


def orphaned_end(text: str) -> bool:
    value = " ".join(re.findall(r"[^\W_]+", text.casefold()))
    # ASR fragments often have no question mark. A question that opens in the
    # final short cue still needs its following answer inside the cut.
    question = re.match(r"^(?:mais )?(?:vous pensez pas|tu penses pas|est ce que|qu est ce que|pourquoi|comment|quel|quelle)\b", value)
    return bool(question and len(value.split()) < 25 and "parce que" not in value and " car " not in value)


def refine_boundaries(model, segments: list[dict], proposal: dict, options: dict) -> tuple[dict, dict]:
    """Choose literal cue anchors; source times never become model indices."""
    first, last = proposal["start_index"], proposal["end_index"]
    lo, hi = segments[first]["start"]-180, segments[last]["end"]+180
    indices = [i for i, row in enumerate(segments) if row["end"] > lo and row["start"] < hi]
    anchors = {f"cue-{i:06d}": i for i in indices}
    starts = [key for key, i in anchors.items() if not orphaned_start(segments[i]["text"])]
    ends = [key for key, i in anchors.items() if not orphaned_end(segments[i]["text"])]
    if not starts or not ends:
        return {**proposal, "usable": False, "reason": "Aucune borne autonome disponible."}, {"kind": "deterministic_boundary_guard"}
    schema = object_schema({"start_anchor": {"enum": starts}, "end_anchor": {"enum": ends},
        "quote_anchor": {"enum": list(anchors)}, "usable": {"type": "boolean"}, "reason": TEXT,
        "title": {"type": "string", "minLength": 1, "maxLength": 110}, "context": TEXT, "essential_nuance": TEXT})
    def valid(value):
        if not value["usable"]:
            return
        a, b, q = (anchors[value[k]] for k in ("start_anchor", "end_anchor", "quote_anchor"))
        if not a <= q <= b or not options["minimum_segment_seconds"] <= segments[b]["end"]-segments[a]["start"] <= options["maximum_segment_seconds"]:
            raise ValueError("Les bornes doivent contenir la citation et respecter les durées permises.")
    rows = [[key, segments[i]["text"]] for key, i in anchors.items()]
    value, proof = model.complete("boundary_refinement",
        "Tu montes un extrait autonome. Choisis des IDENTIFIANTS cue-... attaches aux paroles, jamais des secondes. "
        "Les lignes sont [identifiant, texte integral]. Aucun temps numerique ne sert a choisir les indices. "
        "La proposition initiale est approximative. Corrige son debut et sa fin pour garder une idee complete. "
        "Le debut doit conserver la question ou le contexte utile. La fin doit conclure la reponse, sans question orpheline. "
        "Seules kept_units sont initialement conservees. Les contextes *_not_in_cut sont HORS MONTAGE : "
        "si la question ou la conclusion y est indispensable, deplace explicitement les ancres pour l'inclure. "
        "Ne confonds pas la presence d'une question dans le contexte avec sa presence dans l'extrait. "
        "Le choix des bornes n'est pas un decoupage en blocs reguliers. Preserve les objections et les incertitudes. "
        "Le titre decrit seulement ce qui sera garde. Si aucune coupe autonome ne convient, usable=false.",
        {"proposal": {k: proposal[k] for k in ("title", "context", "essential_nuance")},
         "current_start_anchor": f"cue-{first:06d}", "current_end_anchor": f"cue-{last:06d}",
         "current_first_words": " ".join(s["text"] for s in segments[first:min(first+4,last+1)]),
         "current_last_words": " ".join(s["text"] for s in segments[max(first,last-3):last+1]),
         "kept_units": [row for row in rows if first <= anchors[row[0]] <= last],
         "context_before_not_in_cut": [row for row in rows if anchors[row[0]] < first],
         "context_after_not_in_cut": [row for row in rows if anchors[row[0]] > last],
         "minimum_seconds": options["minimum_segment_seconds"], "maximum_seconds": options["maximum_segment_seconds"]},
        schema, validator=valid)
    return {**value, "start_index": anchors[value["start_anchor"]], "end_index": anchors[value["end_anchor"]],
            "quote_index": anchors[value["quote_anchor"]]}, proof


def selection(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    from .runtime import episode_record_id
    options, segments = settings(config), _segments(episode)
    model, directory = _model(store, episode, config), _directory(store, episode)
    key = job["payload"]["local_run_key"]
    chunks, candidates, seen, accepted_ranges = [], [], set(), []
    interval = max(options["chunk_seconds"], options["maximum_segment_seconds"]+60)
    for indices in windows(segments, interval, options["maximum_segment_seconds"]):
        a, b = segments[indices[0]]["start"], segments[indices[-1]]["end"]
        pictures = samples(Path(episode["source"]), directory / "source-frames", [[a, b]],
                           max(options["frame_interval_seconds"], int((b-a)/options["maximum_images_per_call"])+1))
        schema = copy.deepcopy(ANALYSIS_SCHEMA)
        for field in ("start_index", "end_index", "quote_index"):
            schema["properties"]["candidates"]["items"]["properties"][field].update(minimum=indices[0], maximum=indices[-1])
        def valid_proposals(value):
            for row in value["candidates"]:
                if not indices[0] <= row["start_index"] <= row["quote_index"] <= row["end_index"] <= indices[-1]:
                    raise ValueError("Les indices inclusifs doivent rester dans le lot et contenir la citation : début <= citation <= fin.")
        result, proof = model.complete("selection", "Tu es monteur éditorial de SANDBOX, podcast IA, logiciel et produit. "
            "Analyse toutes les unités et les images fournies. Propose zéro ou plusieurs passages autonomes utiles, sans quota. "
            "Garde le contexte et les objections, sans inventer de faits ni nommer une personne sans preuve. "
            "Les bornes sont des indices absolus d'unités inclusives, jamais des secondes ni des numéros de mots. "
            "Chaque ligne de units suit unit_columns : index, début en secondes, fin en secondes, texte intégral. "
            "Utilise exclusivement les index fournis. start_index <= quote_index <= end_index. "
            "Écris des raisons concises et littérales, sans interprétation symbolique inventée. "
            "Ne transforme pas chaque phrase en extrait ; conserve une explication complète avec sa réserve. "
            "Prévois aussi un extrait horizontal développé de 5 à 15 minutes lorsqu'un sujet cohérent le justifie, sans rallonger un passage artificiellement. "
            "Un passage doit développer une idée, pas seulement annoncer un sujet. Choisis seulement les réseaux pertinents.",
            {"episode_title": episode["title"], "unit_columns": ["index", "start_seconds", "end_seconds", "text"],
             "units": [[i, round(segments[i]["start"], 3), round(segments[i]["end"], 3), segments[i]["text"]] for i in indices], "images": pictures,
             "index_range": [indices[0], indices[-1]], "minimum_seconds": options["minimum_segment_seconds"], "maximum_seconds": options["maximum_segment_seconds"]},
            schema, images=[Path(x["path"]) for x in pictures], validator=valid_proposals)
        chunks.append({"start_seconds": a, "end_seconds": b, "indices": indices, "summary": result["summary"], "evidence": proof, "images": pictures})
        for proposal in result["candidates"]:
            original_proposal = proposal
            boundaries, boundary_proof = refine_boundaries(model, segments, proposal, options)
            if boundaries["usable"]:
                proposal = {**proposal, **{name: boundaries[name] for name in
                            ("start_index", "end_index", "quote_index", "title", "context", "essential_nuance")}}
            first, last, quote = (proposal[x] for x in ("start_index", "end_index", "quote_index"))
            if not 0 <= first <= quote <= last < len(segments):
                raise LocalModelError("local_candidate_indices_invalid")
            start, end = segments[first]["start"], segments[last]["end"]
            if boundaries["usable"] and not options["minimum_segment_seconds"] <= end-start <= options["maximum_segment_seconds"]:
                raise LocalModelError("local_refined_duration_invalid")
            cut_key = digest({"source": episode["source_sha256"], "start": start, "end": end})
            if cut_key in seen:
                continue
            if boundaries["usable"]:
                seen.add(cut_key)
            candidate = {**proposal, "segment_id": episode_record_id(store, "candidate", "local-"+cut_key[:20], episode["episode_id"]),
                         "episode_id": episode["episode_id"], "source_sha256": episode["source_sha256"],
                         "episode_revision": episode["revision"], "local_run_key": key, "local_only": True,
                         "start_seconds": start, "end_seconds": end, "decision": "needs_review",
                         "cuts": [{"source_start_seconds": start, "source_end_seconds": end}],
                         "content_evidence": {"evidence_id": "spoken-"+str(quote), "quote": segments[quote]["text"],
                             "start_seconds": segments[quote]["start"], "end_seconds": segments[quote]["end"],
                             "context": proposal["context"], "supports": proposal["rationale"]}, "generation_evidence": proof,
                         "boundary_refinement": {"original_proposal": original_proposal, "result": boundaries, "evidence": boundary_proof}}
            if not boundaries["usable"]:
                candidate.update(decision="archived", rejection_reason="no_autonomous_boundaries")
                candidates.append(candidate)
                continue
            if any(max(0, min(end, b)-max(start, a)) > .8*min(end-start, b-a) for a, b in accepted_ranges):
                candidate.update(decision="archived", rejection_reason="overlapping_editorial_alternative",
                                 local_editorial_review={"passed": False, "batches": [], "scope": "not_performed_already_retained_alternative"})
                candidates.append(candidate)
                continue
            # Editorial selection reads all the words plus representative raw
            # frames. Dense visual inspection belongs to the final rendered
            # asset (quality), where every five-second sample is still reviewed.
            selected_pictures = samples(Path(episode["source"]), directory / "source-frames", [[start, end]],
                max(options["review_frame_interval_seconds"], int((end-start)/options["maximum_images_per_call"])+1))
            review = review_images(model, "selection_review", selected_pictures,
                {"candidate": {k: candidate[k] for k in ("title", "audience", "context", "rationale", "essential_nuance", "start_seconds", "end_seconds", "format")},
                 "cut_first_words": " ".join(u["text"] for u in segments[first:min(first+4,last+1)]),
                 "cut_last_words": " ".join(u["text"] for u in segments[max(first,last-3):last+1]),
                 "source_units_columns": ["start_seconds", "end_seconds", "text"],
                 "source_units": [[round(u["start"], 3), round(u["end"], 3), u["text"]] for u in segments[first:last+1]],
                 "context_before_not_in_cut": [[round(u["start"], 3), round(u["end"], 3), u["text"]] for u in segments[max(0, first-6):first]],
                 "context_after_not_in_cut": [[round(u["start"], 3), round(u["end"], 3), u["text"]] for u in segments[last+1:last+7]]},
                ("faithfulness", "context_preserved", "standalone_value", "start_self_contained", "end_complete", "visual_usable"))
            candidate.update(decision="retained" if review["passed"] else "needs_review", local_editorial_review=review)
            if review["passed"]:
                accepted_ranges.append((start, end))
            candidates.append(candidate)
    # Collapse overlapping alternatives rather than manufacturing a content quota.
    retained_ranges = []
    for candidate in candidates:
        if candidate["decision"] == "retained":
            start, end = candidate["start_seconds"], candidate["end_seconds"]
            if any(max(0, min(end, b)-max(start, a)) > .8*min(end-start, b-a) for a, b in retained_ranges):
                candidate.update(decision="archived", rejection_reason="overlapping_editorial_alternative")
            else:
                retained_ranges.append((start, end))
    if fingerprint(Path(episode["transcript"])) != episode["transcript_sha256"]:
        raise LocalModelError("local_transcript_changed")
    analysis = {"episode_id": episode["episode_id"], "local_run_key": key, "source_sha256": episode["source_sha256"],
                "transcript_sha256": episode["transcript_sha256"], "candidates": candidates, "chunks": chunks,
                "coverage": {"transcript": {"segments_read": len(segments), "complete_supplied_text": True},
                             "visual": {"scope": "point_samples", "continuous_viewing": False},
                             "audio": {"scope": "automatic_transcription", "human_listening": False}},
                "speaker_identification": "not_certified", "synthetic": episode.get("synthetic", False),
                "blockers": [], "local_only": True}
    write_json(directory / ("analysis-"+key+".json"), analysis)
    with store.transaction():
        store.put("analysis", episode["episode_id"], analysis, episode_id=episode["episode_id"], now=now)
        current_ids = {c["segment_id"] for c in candidates}
        for old in store.records("candidate", episode["episode_id"]):
            if old.get("local_only") and (old.get("local_run_key") != key or old["segment_id"] not in current_ids):
                old.update(decision="archived", rejection_reason="superseded_local_revision")
                store.put("candidate", old["segment_id"], old, episode_id=episode["episode_id"], now=now)
        for candidate in candidates:
            store.put("candidate", candidate["segment_id"], candidate, episode_id=episode["episode_id"], now=now)
            if candidate["decision"] == "retained":
                store.enqueue("local_render", episode["episode_id"], payload(episode, config, segment_id=candidate["segment_id"],render_profile=RENDER_PROFILE), now=now)
    return {"candidates": len(candidates), "retained": len(retained_ranges), "chunks": len(chunks)}


def recheck(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    candidate = store.get("candidate", job["payload"]["segment_id"])
    if (not candidate or candidate.get("local_editorial_revision") != job["payload"].get("editorial_revision")
            or candidate.get("decision") == "archived"):
        return {"status": "superseded"}
    verify_evidence_files(candidate["local_edit_plan"])
    rows = [r for r in _segments(episode) if candidate["start_seconds"] <= r["start"] and r["end"] <= candidate["end_seconds"]]
    options = settings(config)
    pictures = samples(Path(episode["source"]), _directory(store, episode) / "source-frames",
                       [[candidate["start_seconds"], candidate["end_seconds"]]],
                       max(options["review_frame_interval_seconds"], int((candidate["end_seconds"]-candidate["start_seconds"])/options["maximum_images_per_call"])+1))
    review = review_images(_model(store, episode, config), "selection_review", pictures,
        {"candidate": {k: candidate[k] for k in ("title", "audience", "context", "rationale", "essential_nuance", "start_seconds", "end_seconds", "format")},
         "cut_first_words": " ".join(r["text"] for r in rows[:4]), "cut_last_words": " ".join(r["text"] for r in rows[-4:]),
         "source_units_columns": ["start_seconds", "end_seconds", "text"],
         "source_units": [[round(r["start"], 3), round(r["end"], 3), r["text"]] for r in rows]},
        ("faithfulness", "context_preserved", "standalone_value", "start_self_contained", "end_complete", "visual_usable"))
    candidate.update(decision="retained" if review["passed"] else "needs_review", local_editorial_review=review)
    store.put("candidate", candidate["segment_id"], candidate, episode_id=episode["episode_id"], now=now)
    if not review["passed"]:
        raise LocalModelError("local_editorial_recheck_failed")
    # Compare source intervals rather than codec-rounded output duration.
    matches = [a for a in store.records("asset", episode["episode_id"]) if a.get("segment_id") == candidate["segment_id"]
               and [(c["source_start_seconds"], c["source_end_seconds"]) for c in a.get("cuts", [])]
               == [(c["source_start_seconds"], c["source_end_seconds"]) for c in candidate["cuts"]]
               and a.get('parameters',{}).get('layout')=='fit_preserve_all_pixels_local_captions_v1' and a.get('qa_status')!='superseded'
               and (not candidate.get('caption_grouping_version') or a.get('parameters',{}).get('subtitle_grouping_version')==candidate['caption_grouping_version'])]
    if matches:
        for asset in matches:
            store.enqueue("local_quality", episode["episode_id"], payload(episode, config, asset_id=asset["asset_id"], editorial_revision=candidate["local_editorial_revision"]), now=now)
    else:
        store.enqueue("local_render", episode["episode_id"], payload(episode, config, segment_id=candidate["segment_id"], editorial_revision=candidate["local_editorial_revision"],render_profile=RENDER_PROFILE), now=now)
    return {"segment_id": candidate["segment_id"], "status": "retained"}


def render_local(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    from .runtime import render_candidate
    candidate = store.get("candidate", job["payload"]["segment_id"])
    if not candidate or candidate.get("local_run_key") != job["payload"]["local_run_key"] or candidate.get("decision") != "retained":
        return {"status": "superseded"}
    if candidate.get('render_profile') != RENDER_PROFILE:
        candidate['render_profile']=RENDER_PROFILE
        store.put('candidate',candidate['segment_id'],candidate,episode_id=episode['episode_id'],now=now)
    asset = render_candidate(store, config, episode["episode_id"], candidate["segment_id"], candidate["format"], now=now)
    asset.update(local_only=True, local_run_key=job["payload"]["local_run_key"], qa_status="needs_review",
                 local_editorial_revision=candidate.get("local_editorial_revision"))
    with store.transaction():
        store.put("asset", asset["asset_id"], asset, episode_id=episode["episode_id"], now=now)
        for row in store.publications(episode["episode_id"]):
            if row["asset_id"] == asset["asset_id"]:
                row.update(local_only=True, local_run_key=job["payload"]["local_run_key"], status="local_preparing", qa_status="needs_review")
                store.save_publication(row, now=now)
        store.enqueue("local_quality", episode["episode_id"], payload(episode, config, asset_id=asset["asset_id"]), now=now)
    return {"asset_id": asset["asset_id"], "path": asset["path"]}


def replace_audio_headroom(store, episode: dict, candidate: dict, asset: dict, config: dict, *, now=None, original=None) -> dict:
    from .local_audio import repair_headroom
    from .packaging import prepare
    from .analytics import ensure_packaging_unlocked
    from .runtime import episode_record_id
    old_packs = [p for p in store.publications(episode["episode_id"]) if p["asset_id"] == asset["asset_id"]]
    for pack in old_packs:
        if not pack.get("local_only") or pack.get("remote_id") or pack.get("scheduled_at"):
            raise LocalModelError("local_audio_repair_remote_intent_refused")
        ensure_packaging_unlocked(pack["id"], store.records("experiment"))
    revised = repair_headroom(original or asset)
    revised.update(**{name: asset.get(name) for name in ("episode_id", "segment_id", "local_run_key", "local_only", "local_editorial_revision")})
    revised["asset_id"] = episode_record_id(store, "asset", revised["asset_id"], episode["episode_id"])
    packs = prepare(episode, candidate, revised, config, store.directory / "episodes" / episode["episode_id"] / "packs")
    with store.transaction():
        asset.update(qa_status="superseded", replacement_asset_id=revised["asset_id"])
        store.put("asset", asset["asset_id"], asset, episode_id=episode["episode_id"], now=now)
        store.put("asset", revised["asset_id"], revised, episode_id=episode["episode_id"], now=now)
        for pack in old_packs:
            pack.update(status="archived", qa_status="superseded", blocked_reason="replaced_for_output_audio_headroom", scheduled_at=None)
            store.save_publication(pack, now=now)
        for pack in packs:
            pack.update(local_only=True, local_run_key=asset["local_run_key"], status="local_preparing", qa_status="needs_review")
            store.put("packaging", pack["id"], pack, episode_id=episode["episode_id"], now=now)
            store.save_publication(pack, now=now)
        args = {"asset_id": revised["asset_id"]}
        if candidate.get("local_editorial_revision"):args["editorial_revision"] = candidate["local_editorial_revision"]
        store.enqueue("local_quality", episode["episode_id"], payload(episode, config, **args), now=now)
        store.event("local_audio_headroom_repaired", asset["asset_id"], {"replacement_asset_id": revised["asset_id"],
            "gain_db": revised['audio_headroom']['gain_db'], 'original_asset_id': (original or asset)['asset_id']}, now=now)
    return {"status": "replaced_for_audio_headroom", "asset_id": revised["asset_id"]}


def quality(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    asset = store.get("asset", job["payload"]["asset_id"])
    candidate = store.get("candidate", asset["segment_id"])
    if not candidate or candidate.get("decision") != "retained" or asset.get("qa_status") == "superseded":
        return {"status": "superseded"}
    if asset.get("local_run_key") != job["payload"]["local_run_key"]:
        return {"status": "superseded"}
    expected = asset["sha256"]
    if fingerprint(Path(asset["path"])) != expected:
        raise LocalModelError("local_render_changed")
    for name, sha in (("subtitle_path", "subtitle_sha256"), ("ass_path", "ass_sha256")):
        if asset.get(name) and fingerprint(Path(asset[name])) != asset.get(sha):
            raise LocalModelError("local_render_subtitles_changed")
    verify_evidence_files(asset.get('subtitle_alignment_evidence',[]))
    checks = technical_checks(asset)
    source_rows = [s for s in _segments(episode) if candidate["start_seconds"] <= s["start"] and s["end"] <= candidate["end_seconds"]]
    model = _model(store, episode, config)
    title_review = title_support(model, candidate["title"], sentences(source_rows))
    boundaries = cut_boundaries(model, _segments(episode), candidate['start_seconds'], candidate['end_seconds'])
    details = asset.get("qa", {}).get("details", {})
    from .local_audio import HEADROOM_VERSION
    headroom = asset.get('audio_headroom')
    if (title_review['passed'] and boundaries['passed'] and headroom and headroom.get('version', 1) < HEADROOM_VERSION
            and asset.get('qa', {}).get('technical') == 'needs_review' and details.get('decode') == 'passed'
            and details.get('max_volume_db') is not None and details['max_volume_db'] > -.1
            and not details.get('black_intervals_seconds') and not details.get('silence_events')):
        original = store.get('asset', headroom['original_asset_id'])
        if (not original or original.get('audio_headroom') or original['sha256'] != headroom['original_sha256']
                or original['source_sha256'] != asset['source_sha256'] or original['cuts'] != asset['cuts']):
            raise LocalModelError('local_audio_original_unavailable')
        return replace_audio_headroom(store, episode, candidate, asset, config, now=now, original=original)
    if (title_review["passed"] and boundaries['passed'] and asset.get("qa", {}).get("technical") == "needs_review" and not asset.get("audio_headroom")
            and details.get("decode") == "passed" and details.get("max_volume_db") is not None and details["max_volume_db"] > -.1
            and not details.get("black_intervals_seconds") and not details.get("silence_events")):
        return replace_audio_headroom(store, episode, candidate, asset, config, now=now)
    if title_review["passed"] and boundaries['passed']:
        audio = audio_correspondence(Path(episode["source"]), asset) if all(checks.values()) else {"passed": False, "scope": "technical_control_failed"}
        pictures = samples(Path(asset["path"]), _directory(store, episode) / "render-frames", [[0, asset["duration_seconds"]]], settings(config)["review_frame_interval_seconds"])
        review = review_images(model, "render_review", pictures,
            {"candidate": {k: candidate[k] for k in ("title", "audience", "essential_nuance", "start_seconds", "end_seconds")},
             "source_units": source_rows, "format": asset["format"], "technical_checks": checks, "audio_correspondence": audio},
            ("faithfulness", "framing_readable", "subtitles_readable", "no_misleading_edit"))
    else:
        audio = {"passed": False, "scope": "not_performed_failed_title_or_boundary"}
        review = {"passed": False, "batches": [], "scope": "not_performed_failed_title_or_boundary"}
    result = {"asset_sha256": expected, "source_sha256": episode["source_sha256"], "transcript_sha256": episode["transcript_sha256"],
              "version": QUALITY_VERSION, "subtitle_sha256": fingerprint(Path(asset["subtitle_path"])), "checks": checks, "title_support": title_review, 'boundaries':boundaries, "audio": audio, "visual_editorial": review,
              "passed": all(checks.values()) and title_review["passed"] and boundaries['passed'] and audio["passed"] and review["passed"], "reviewed_at": iso(now or utcnow()),
              "human_review": False, "local_only": True, "editorial_revision": candidate.get("local_editorial_revision")}
    if fingerprint(Path(asset["path"])) != expected or fingerprint(Path(episode["source"])) != episode["source_sha256"]:
        raise LocalModelError("local_quality_input_changed")
    path = _directory(store, episode) / ("quality-"+digest(result)+".json")
    write_json(path, result)
    asset.update(qa_status="local_passed" if result["passed"] else "local_failed", local_quality_version=QUALITY_VERSION, local_quality={**result, "path": str(path), "sha256": fingerprint(path)})
    store.put("asset", asset["asset_id"], asset, episode_id=episode["episode_id"], now=now)
    for row in store.publications(episode["episode_id"]):
        if row["asset_id"] == asset["asset_id"]:
            row.update(qa_status=asset["qa_status"], blocked_reason=None if result["passed"] else "local_quality_failed")
            store.save_publication(row, now=now)
    if not result["passed"]:
        raise LocalModelError("local_quality_failed")
    next_stage = {"asset_id": asset["asset_id"], "packaging_version": PACKAGING_VERSION, 'quality_version':QUALITY_VERSION}
    if candidate.get("local_editorial_revision"):
        next_stage["editorial_revision"] = candidate["local_editorial_revision"]
    packs = [p for p in store.publications(episode['episode_id']) if p['asset_id']==asset['asset_id'] and p['status'] not in {'archived','cancelled'}]
    if not packs or not all(p.get('status')=='local_ready' and p.get('local_packaging_version')==PACKAGING_VERSION for p in packs):
        store.enqueue("local_thumbnails", episode["episode_id"], payload(episode, config, **next_stage), now=now)
    return {"asset_id": asset["asset_id"], "quality_path": str(path), "status": "local_passed"}


def punctuation(value: str) -> str:
    return value.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "«": '"', "»": '"', "—": "-", "–": "-"}))


CONCEPT_SCHEMA = object_schema({"angle": TEXT, "hypothesis": TEXT,
    "video_title": {"type": "string", "minLength": 1, "maxLength": 100},
    "thumbnail_text": {"type": "string", "minLength": 1, "maxLength": 200},
    "wording_reason": TEXT, "title_image_complementarity": TEXT, "visual_rationale": TEXT,
    "frame_index": {"type": "integer", "minimum": 0}, "spoken_unit_index": {"type": "integer", "minimum": 0}})
PACKAGING_SCHEMA = object_schema({"viewer_question": TEXT, "content_promise": TEXT,
    "selection_reason": TEXT, "preferred_index": {"type": "integer", "minimum": 0, "maximum": 2},
    "concepts": {"type": "array", "minItems": 3, "maxItems": 3, "items": CONCEPT_SCHEMA},
    "platform_texts": object_schema({name: {"type": "string", "minLength": 1, "maxLength": 1200}
                                     for name in ("youtube", "instagram", "tiktok", "x", "linkedin")})})


def anchor_words(text: str) -> list[str]:
    from .thumbnails import _normalized
    stop = {"nous", "vous", "elles", "leur", "leurs", "pour", "avec", "alors", "ensuite", "permet", "faire", "faut", "doit", "doivent",
            "peut", "peuvent", "etre", "avoir", "dans", "pendant", "avant", "apres", "cette", "ceci", "cela", "mais", "donc", "plus", "toute", "toutes", "tout", "tous",
            "remarque", "pense", "pensais", "sais", "sait", "dire", "trouve", "quelque", "chose", "aussi", "quand", "comment", "comme", "vraiment"}
    return sorted({w for w in re.findall(r"[^\W\d_]+", _normalized(text)) if len(w) >= 4 and w not in stop})


def anchor_present(term: str, text: str) -> bool:
    return any(word == term or word == term+"s" or word+"s" == term for word in anchor_words(text))


def validate_local_wording(response: dict, config: dict, spoken_units=None, concept_plan=None, prior_concepts=None) -> None:
    from .thumbnails import _font, _wrap, _normalized
    scale = config.get("thumbnails", {}).get("width", 3840)/1280
    for index, row in enumerate(response["concepts"]):
        phrase = punctuation(row["thumbnail_text"])
        for previous in prior_concepts or []:
            if (any(_normalized(row[k]) == _normalized(previous[k]) for k in ("angle", "hypothesis"))
                    or _normalized(phrase).strip('.?! ') == _normalized(previous['thumbnail_text']).strip('.?! ')
                    or (_normalized(row["video_title"]),_normalized(phrase)) == (_normalized(previous["video_title"]),_normalized(previous["thumbnail_text"]))):
                raise ValueError("Tu recopies un concept précédent ('"+previous["video_title"]+"'). Rédige uniquement l'idée précise du plan actuel, avec son propre angle et sa propre hypothèse, sans réutiliser ceux de prior_concepts.")
        if concept_plan:
            plan = next(p for p in concept_plan["concepts"] if p["concept_index"] == index)
            if not anchor_present(plan["anchor_term"], row["video_title"]+" "+phrase):
                raise ValueError("Le titre ou la phrase d'image doit nommer explicitement le mot concret '"+plan["anchor_term"]+"', au singulier ou au pluriel. Réécris ce couple autour de ce mot, sans le remplacer par un autre objet.")
        words = phrase.casefold().strip(" .?!,:;\"'").split()
        if not words or words[-1] in {"le", "la", "les", "un", "une", "de", "du", "des", "au", "aux", "que", "qui", "dont", "ne", "et", "ou", "par", "pour", "à", "en"}:
            raise ValueError("Réécris les trois phrases de miniature en formulations autonomes, sans article ou négation inachevée à la fin.")
        if spoken_units:
            quote = next(u["text"] for u in spoken_units if u["index"] == row["spoken_unit_index"])
            if len(words) >= 5 and _normalized(quote).startswith(_normalized(phrase)) and _normalized(quote) != _normalized(phrase):
                raise ValueError("Réécris les trois phrases en formulations courtes et complètes. Ne recopie pas le début tronqué d'une citation.")
        if _normalized(phrase).strip(".?! ") == _normalized(row["video_title"]).strip(".?! "):
            raise ValueError("La phrase de l'image doit compléter le titre, sans le répéter.")
        for size in range(112, 47, -2):
            wrapped = _wrap(phrase, _font(round(size*scale)), 440*scale)
            if wrapped and len(wrapped) <= 3 and len(wrapped)*size*1.18 <= 430:
                break
        else:
            raise ValueError("La phrase de miniature ne tient pas dans trois lignes lisibles. Réécris-la plus brièvement, avec des mots plus courts.")


def align_concept_evidence(model, concepts: list[dict], spoken_units: list[dict]) -> tuple[dict, dict]:
    alternatives = []
    for index, concept in enumerate(concepts):
        indices = [u["index"] for u in spoken_units if len(u["text"].split()) >= 12 and concept["anchor_term"] in anchor_words(u["text"])]
        alternatives.append(object_schema({"concept_index": {"const": index}, "spoken_unit_index": {"enum": indices},
            "supported": {"type": "boolean"}, "reason": {"type": "string", "minLength": 1, "maxLength": 600}}))
    schema = object_schema({"assignments": {"type": "array", "minItems": 3, "maxItems": 3,
        "items": {"anyOf": alternatives}}})
    def distinct(value):
        if {a["concept_index"] for a in value["assignments"]} != {0, 1, 2}:
            raise ValueError("Examiner chacun des trois concepts exactement une fois.")
    return model.complete("citation_alignment", "Tu vérifies indépendamment le lien entre une promesse de miniature et les paroles. "
        "Pour chaque concept, choisis dans les unités la citation qui soutient le plus directement le sens précis du couple titre/image. "
        "Ne confonds pas intégrité technique d'un fichier et fidélité du sens d'un propos. Ne réutilise pas par défaut le choix du rédacteur. "
        "Si aucune citation ne soutient une promesse, supported=false : il faut réécrire le concept, jamais inventer une preuve. "
        "Explique le rapport sémantique précis, pas seulement la présence de mots communs.",
        {"concepts": concepts, "spoken_units": spoken_units}, schema, validator=distinct)


def validate_editorial_question(question: str, source_text: str) -> None:
    if not isinstance(question,str) or not question.rstrip().endswith('?'):
        raise ValueError('Écris une question courte et complète, terminée par un point d\'interrogation. Reformule au lieu de couper à la limite de taille.')
    if any('\u3400'<=char<='\u9fff' and char not in source_text for char in question):
        raise ValueError('Réécris la question en français, sans caractère parasite absent des paroles source.')


def plan_concepts(model, spoken_units: list[dict], candidate: dict, feedback=None) -> tuple[dict, dict]:
    eligible = [u for u in spoken_units if len(u["text"].split()) >= 12 and anchor_words(u['text'])]
    if not eligible:
        raise LocalModelError("local_source_concrete_anchors_missing")
    schema = object_schema({"concepts": {"type": "array", "minItems": 3, "maxItems": 3, "items": object_schema({
        "concept_index": {"enum": [0, 1, 2]}, "spoken_unit_index": {"enum": [u["index"] for u in eligible]}})}})
    def distinct(value):
        if {p["concept_index"] for p in value["concepts"]} != {0, 1, 2}:
            raise ValueError("Planifier chaque concept exactement une fois.")
    return model.complete("concept_plan", "Prépare le plan de trois présentations différentes d'un extrait SANDBOX. "
        "Choisis uniquement trois unités de paroles à mettre en avant. Lis les propos et distingue des idées précises réellement présentes. "
        "Sépare par exemple un mécanisme, un exemple et une réserve lorsqu'ils existent. Réutilise une unité seulement si elle contient plusieurs idées distinctes. "
        "Ne mélange pas toutes les idées dans chaque concept et ne renomme pas trois fois une même hypothèse. "
        "Ne fabrique pas une critique ou des limites pour obtenir trois angles : une réserve doit être réellement exprimée. "
        "Préserve explicitement les 'je ne sais pas', suppositions et anecdotes : une succession observée ne démontre pas sa cause ni le fonctionnement interne. "
        "Ne rédige aucune question, titre ou phrase. Si la critique précédente signale un mélange ou une preuve inadéquate, corrige le choix des unités.",
        {"spoken_units": spoken_units, "audience": candidate["audience"], 'essential_nuance':candidate['essential_nuance'],
         "prior_review_feedback": feedback}, schema, validator=distinct)


def design_concepts(model, candidate: dict, spoken_units: list[dict], frames: list[dict],
                    concept_plan: dict, references: list[dict], config: dict, feedback=None) -> tuple[dict, dict]:
    """One bounded writing task per idea prevents cross-concept evidence mixing."""
    concepts, receipts = [], []
    for index in range(3):
        plan = next(p for p in concept_plan["concepts"] if p["concept_index"] == index)
        unit = next(u for u in spoken_units if u["index"] == plan["spoken_unit_index"])
        schema = copy.deepcopy(CONCEPT_SCHEMA)
        for field in ("frame_index", "visual_rationale", "angle", "hypothesis", "wording_reason", "title_image_complementarity"):
            del schema["properties"][field]
            schema["required"].remove(field)
        schema["properties"]["spoken_unit_index"] = {"const": unit["index"]}
        anchors=[word for word in anchor_words(unit['text']) if word not in {c['anchor_term'] for c in concepts}]
        if not anchors:raise LocalModelError('local_distinct_source_terms_missing')
        schema['properties']['anchor_term']={'enum':anchors}
        schema['required'].append('anchor_term')
        concept, proof = model.complete("packaging_concept",
            "Rédige UN seul couple titre/image SANDBOX à partir du plan et de SA citation. "
            "Le public est francophone : tous les titres, phrases d'image et justifications sont en français naturel. "
            "Conserve les noms propres et termes techniques établis, sans traduire les noms d'outils, mais jamais une phrase entière en anglais ou en franglais. "
            "Les paroles sont les seules preuves de contenu ; les références guident la composition. "
            "Présente une idée précise réellement présente dans cette citation, sans répéter les couples précédents ni fusionner toutes ses idées. "
            "Choisis anchor_term dans les mots autorisés de CETTE citation. Le titre ou la phrase d'image doit nommer explicitement ce mot, au singulier ou au pluriel. "
            "thumbnail_text est un groupe nominal autonome de deux à cinq mots courts, qui complète le titre. "
            "La photo sera un portrait authentique : ne prescris ni schéma, ni interface, ni démonstration visuelle inexistante. "
            "Ne tronque jamais une citation et ne promets ni résultat ni garantie absent des propos. "
            "Un titre qui annonce des limites, risques ou critiques doit avoir une réserve explicitement formulée dans sa citation. "
            "Préserve le sens du lien décrit : ne transforme pas un moyen de comprendre en cause d'un risque. "
            "Sépare intégrité d'un fichier et fidélité du sens. Préserve la réserve essentielle du candidat. "
            "La photo sera extraite automatiquement du passage et contrôlée lors d'une revue visuelle distincte. "
            "N'invente pas de scène ou de démonstration et ne transforme pas l'habillage de la vidéo en sujet.",
            {"plan": plan, "spoken_unit": unit, "audience": candidate['audience'], 'essential_nuance': candidate['essential_nuance'],
             "used_title_image_pairs": [{k:c[k] for k in ('video_title','thumbnail_text')} for c in concepts],
             'allowed_anchor_terms':anchors,
             "generation_constraints_version": 3,
             "references": [{"observation": r["visual_observation"], "takeaway": r["takeaway"]} for r in references],
             "prior_review_feedback": feedback}, schema,
            validator=lambda row, p=plan: validate_local_wording({"concepts": [{**row, 'angle':row['anchor_term'], 'hypothesis':row['anchor_term']}]}, config, spoken_units,
                {"concepts": [{**p, "concept_index": 0,'anchor_term':row['anchor_term']}]}, prior_concepts=concepts))
        question='Que dit l\'extrait à propos de "'+concept['anchor_term']+'" ?'
        concept.update(angle=concept['anchor_term'],hypothesis=concept['anchor_term'],editorial_question=question)
        midpoint = (unit["start"]+unit["end"])/2
        concept["frame_index"] = min(range(len(frames)), key=lambda i: abs(frames[i]["time_seconds"]-midpoint))
        concept["visual_rationale"] = "Photo authentique d'un participant dans le passage cité, recadrée sans modifier son expression ; illustration de la discussion, sans prétendre démontrer l'action racontée."
        concepts.append(concept)
        receipts.append(proof)
    metadata_schema = object_schema({'preferred_index':{'type':'integer','minimum':0,'maximum':2}})
    metadata, evidence = model.complete("packaging",
        "Choisis uniquement le concept préféré pour sa clarté éditoriale, jamais sur une performance non mesurée. "
        "Les titres et phrases sont déjà rédigés : ne les réécris pas et n'ajoute aucun diagnostic sur les propos.",
        {"concepts":concepts,'audience':candidate['audience']},metadata_schema)
    return {**metadata, "concepts": concepts}, {**evidence, "concept_receipts": receipts}


def source_bound_metadata(response: dict, candidate: dict, spoken_units: list[dict]) -> dict:
    """Frame the copy with questions and literal words, never generated diagnoses."""
    result=copy.deepcopy(response)
    for concept in result['concepts']:
        question=concept['editorial_question']
        unit=next(u for u in spoken_units if u['index']==concept['spoken_unit_index'])
        concept.update(angle=question,hypothesis='Question éditoriale : '+question,
            wording_reason='Paroles conservées : "'+punctuation(unit['text'])+'"',
            title_image_complementarity='Le titre présente la question "'+question+'". L\'accroche "'+punctuation(concept['thumbnail_text'])+'" en propose une entrée courte avec un portrait du passage.')
    selected=result['concepts'][result['preferred_index']]
    unit=next(u for u in spoken_units if u['index']==selected['spoken_unit_index'])
    result.update(viewer_question=selected['editorial_question'],
        content_promise='Une discussion autour du sujet : "'+punctuation(candidate['title'])+'".',
        selection_reason='Choix éditorial initial autour de la question : '+selected['editorial_question']+' Aucune performance mesurée.',
        metadata_mode='source_bound_v1')
    base=punctuation(selected['video_title'])
    quote=punctuation(unit['text'])
    result['platform_texts']={}
    for platform in ('youtube','instagram','tiktok','x','linkedin'):
        limit=280 if platform=='x' else 1200
        text=base+'\n\nDans cet extrait : "'+quote+'"'
        result['platform_texts'][platform]=text if len(text)<=limit else base+'\n\nUn passage de notre discussion SANDBOX.'
    return result


def packaging_units(rows: list[dict]) -> list[dict]:
    """Keep short filler introductions with adjacent speech, within one kept cut."""
    units = sentences(rows)
    result, pending = [], None
    for unit in units:
        if pending is not None:
            if unit["start"]-pending["end"] <= 5 and unit["end"]-pending["start"] <= 80 and len(pending["text"])+len(unit["text"]) <= 1400:
                unit = {"start": pending["start"], "end": unit["end"], "text": pending["text"]+" "+unit["text"]}
            else:
                result.append(pending)
            pending = None
        if len(unit["text"].split()) < 30:
            pending = unit
        else:
            result.append(unit)
    if pending is not None:
        if result and pending["start"]-result[-1]["end"] <= 5 and pending["end"]-result[-1]["start"] <= 80 and len(result[-1]["text"])+len(pending["text"]) <= 1400:
            result[-1] = {"start": result[-1]["start"], "end": pending["end"], "text": result[-1]["text"]+" "+pending["text"]}
        else:
            result.append(pending)
    complete=[]
    for unit in result:
        continuation=re.match(r'^(?:que|qui|dont|parce que|mais|si|sauf|à condition|même si)\b',unit['text'].strip(),flags=re.IGNORECASE)
        if (complete and continuation and unit['start']-complete[-1]['end']<=5
                and unit['end']-complete[-1]['start']<=80 and len(complete[-1]['text'])+len(unit['text'])<=1400):
            complete[-1]={'start':complete[-1]['start'],'end':unit['end'],'text':complete[-1]['text']+' '+unit['text']}
        else:complete.append(unit)
    return complete


def frame_crop(model, frame: dict) -> tuple[list[float], dict]:
    from .local_faces import choose_portrait
    return choose_portrait(model, frame)


def portrait_frame(model, frames, preferred):
    """Try nearby real frames after an unusable portrait, with a bounded search."""
    last_error = None
    for index in sorted(range(len(frames)), key=lambda i: abs(frames[i]["time_seconds"]-frames[preferred]["time_seconds"]))[:3]:
        try:
            crop, proof = frame_crop(model, frames[index])
            return index, crop, proof
        except LocalModelError as error:
            if str(error) not in {"local_thumbnail_face_not_detected", "local_thumbnail_face_not_usable"}:
                raise
            last_error = error
    raise last_error or LocalModelError("local_thumbnail_face_not_detected")


def supersede_bundles(store, asset, keep=None, *, now=None):
    """Runtime status changes preserve the immutable original media receipts."""
    for bundle in store.records("thumbnail_bundle", asset["episode_id"]):
        if bundle['segment_id']==asset['segment_id'] and bundle["asset_sha256"] == asset["sha256"] and bundle["bundle_id"] != keep and bundle.get("review_status") != "superseded":
            bundle.update(previous_review_status=bundle["review_status"], review_status="superseded", replacement_bundle_id=keep)
            store.put("thumbnail_bundle", bundle["bundle_id"], bundle, episode_id=asset["episode_id"], now=now)


def assert_local_asset(episode: dict, asset: dict) -> None:
    review = asset.get("local_quality", {})
    if (asset.get("qa_status") != "local_passed" or not review.get("passed") or review.get("asset_sha256") != asset["sha256"]
            or asset.get('local_quality_version') != QUALITY_VERSION or review.get('version') != QUALITY_VERSION
            or asset.get("local_editorial_revision") != review.get("editorial_revision")
            or review.get("source_sha256") != episode["source_sha256"] or review.get("transcript_sha256") != episode["transcript_sha256"]
            or fingerprint(Path(asset["path"])) != asset["sha256"]
            or fingerprint(Path(asset["subtitle_path"])) != review.get("subtitle_sha256")
            or asset.get('ass_path') and fingerprint(Path(asset['ass_path'])) != asset.get('ass_sha256')
            or fingerprint(Path(episode["transcript"])) != episode["transcript_sha256"]
            or fingerprint(Path(review["path"])) != review["sha256"]):
        raise LocalModelError("local_asset_review_changed")
    verify_review_files(review["visual_editorial"])
    verify_evidence_files(review.get("title_support", {}))
    verify_evidence_files(review.get('boundaries',{}))
    verify_evidence_files(asset.get('subtitle_alignment_evidence',[]))


def request_packaging_revision(store, config: dict, asset_id: str, reviewer: str, notes: list[str], *, now=None) -> dict:
    """Invalidate one local packaging without changing the approved media."""
    from .local_models import validate
    from .analytics import ensure_packaging_unlocked
    review=validate({'reviewer':reviewer,'notes':notes},object_schema({'reviewer':TEXT,
        'notes':{'type':'array','minItems':1,'maxItems':20,'items':TEXT}}))
    asset=store.get('asset',asset_id)
    if not asset or not asset.get('local_only'):raise ValueError('Média local requis.')
    episode=store.get('episode',asset['episode_id']);assert_local_asset(episode,asset)
    candidate=store.get('candidate',asset['segment_id'])
    if not candidate or candidate.get('decision')!='retained':raise ValueError('Passage retenu requis.')
    args={'asset_id':asset_id,'packaging_version':PACKAGING_VERSION,'quality_version':QUALITY_VERSION,'review_feedback':review}
    if candidate.get('local_editorial_revision'):args['editorial_revision']=candidate['local_editorial_revision']
    job_payload=payload(episode,config,**args)
    identity=digest({'kind':'local_thumbnails','episode_id':episode['episode_id'],'payload':job_payload})
    if any(j['id']==identity for j in store.jobs()):return {'status':'already_requested','job_id':identity}
    with store.transaction():
        if any(j['status']=='running' and j['payload'].get('asset_id')==asset_id for j in store.jobs()):
            raise ValueError('Attendre la fin du traitement de ce média.')
        packs=[p for p in store.publications(episode['episode_id']) if p['asset_id']==asset_id]
        if any(not p.get('local_only') or p.get('remote_id') or p.get('scheduled_at') for p in packs):
            raise ValueError('Une intention distante interdit cette correction locale.')
        for pack in packs:ensure_packaging_unlocked(pack['id'],store.records('experiment'))
        for job in store.jobs():
            if job['kind']=='local_thumbnails' and job['payload'].get('asset_id')==asset_id and job['status'] in {'queued','blocked','failed'}:
                store.db.execute("UPDATE jobs SET status='cancelled',last_error='superseded_by_review_feedback' WHERE id=?",(job['id'],))
        supersede_bundles(store,asset,now=now)
        for pack in packs:
            pack.update(status='local_preparing',packaging_status='needs_review',blocked_reason='packaging_review_feedback',proposed_at=None)
            store.save_publication(pack,now=now)
        calendar_record=store.get('local_calendar',episode['episode_id'])
        if calendar_record:
            calendar_record.update(status='running',previous_planned=calendar_record.get('planned',[]),planned=[],valid_for_publication=False)
            store.put('local_calendar',episode['episode_id'],calendar_record,episode_id=episode['episode_id'],now=now)
        store.enqueue('local_thumbnails',episode['episode_id'],job_payload,now=now)
        store.event('local_packaging_revision_requested',asset_id,{'job_id':identity,'review_feedback':review},now=now)
    return {'status':'queued','job_id':identity}


def thumbnails(store, episode: dict, config: dict, job: dict, *, now=None, attempt=0, feedback=None) -> dict:
    from .analytics import ensure_packaging_unlocked
    from .packaging import revision
    from .thumbnails import create_bundle, bundle_digest
    if job["payload"].get("packaging_version") != PACKAGING_VERSION or job['payload'].get('quality_version') != QUALITY_VERSION:
        return {"status": "superseded"}
    asset = store.get("asset", job["payload"]["asset_id"])
    assert_local_asset(episode, asset)
    if feedback is None and job['payload'].get('review_feedback'):
        feedback=job['payload']['review_feedback']
    candidate = store.get("candidate", asset["segment_id"])
    verify_review_files(candidate["local_editorial_review"])
    verify_evidence_files(candidate.get("boundary_refinement", {}))
    verify_evidence_files(candidate.get("local_edit_plan", {}))
    packs = [p for p in store.publications(episode["episode_id"]) if p["asset_id"] == asset["asset_id"]]
    if any(not p.get('local_only') or p.get('remote_id') or p.get('scheduled_at') for p in packs):
        raise LocalModelError('local_packaging_remote_intent_refused')
    for pack in packs:
        ensure_packaging_unlocked(pack["id"], store.records("experiment"))
    options, directory, model = settings(config), _directory(store, episode), _model(store, episode, config)
    registry = Path(options["reference_registry"])
    registry = registry if registry.is_absolute() else ROOT / registry
    references = load_json(registry)["references"]
    frames = samples(Path(episode["source"]), directory / "source-frames", [[candidate["start_seconds"], candidate["end_seconds"]]],
                     max(options["review_frame_interval_seconds"], int((candidate["end_seconds"]-candidate["start_seconds"])/options["maximum_images_per_call"])+1))
    spoken_units = []
    source_segments = _segments(episode)
    for cut in asset["cuts"]:
        rows = [s for s in source_segments if cut["source_start_seconds"] <= s["start"] and s["end"] <= cut["source_end_seconds"]]
        for unit in packaging_units(rows):
            spoken_units.append({"index": len(spoken_units), **unit})
    if not spoken_units:
        raise LocalModelError("local_packaging_spoken_evidence_missing")
    concept_plan, plan_evidence = plan_concepts(model, spoken_units, candidate, feedback)
    compact_candidate = {name: candidate[name] for name in ("title", "audience", "rationale", "context", "essential_nuance")}
    response, evidence = design_concepts(model, compact_candidate, spoken_units, frames,
                                         concept_plan, references, config, feedback)
    alignment, alignment_proof = align_concept_evidence(model, response["concepts"], spoken_units)
    unsupported = [a for a in alignment["assignments"] if not a["supported"]]
    if unsupported:
        if attempt+1 < options["maximum_model_attempts"]:
            return thumbnails(store, episode, config, job, now=now, attempt=attempt+1, feedback=unsupported)
        raise LocalModelError("local_concept_not_supported_by_speech")
    for assignment in alignment["assignments"]:
        response["concepts"][assignment["concept_index"]]["spoken_unit_index"] = assignment["spoken_unit_index"]
    response=source_bound_metadata(response,candidate,spoken_units)
    concepts, content_evidence, crops = [], [], {}
    for index, row in enumerate(response["concepts"]):
        if row["frame_index"] >= len(frames):
            raise LocalModelError("local_thumbnail_frame_index_invalid")
        unit = next(u for u in spoken_units if u["index"] == row["spoken_unit_index"])
        midpoint = (unit["start"]+unit["end"])/2
        row["frame_index"] = min(range(len(frames)), key=lambda i: abs(frames[i]["time_seconds"]-midpoint))
        if row["frame_index"] not in crops:
            selected_index, crop, crop_evidence = portrait_frame(model, frames, row["frame_index"])
            crops[row["frame_index"]] = (selected_index, crop, crop_evidence)
        selected_index, crop, crop_evidence = crops[row["frame_index"]]
        row["frame_index"] = selected_index
        evidence_id = "concept-"+str(index+1)+"-spoken-"+str(row["spoken_unit_index"])
        content_evidence.append({"evidence_id": evidence_id, "quote": unit["text"], "start_seconds": unit["start"],
                                 "end_seconds": unit["end"], "context": candidate["context"], "supports": row["hypothesis"]})
        concepts.append({**{k: punctuation(v) if isinstance(v, str) else v for k, v in row.items()},
            "concept_id": "concept-"+str(index+1), "reference_ids": [r["reference_id"] for r in references],
            "evidence_ids": [evidence_id],
            "image": {"kind": "episode_frame", "source_time_seconds": frames[row["frame_index"]]["time_seconds"],
                      "crop": crop, "focus_box": crop}, "crop_evidence": crop_evidence,
            "image_box": [60, 90, 620, 540], "text_box": [730, 120, 440, 430]})
    brief = {"version": 1, "episode_id": episode["episode_id"], "segment_id": candidate["segment_id"],
             "asset_sha256": asset["sha256"], "source_sha256": episode["source_sha256"],
             "created_by": "local-creator:"+evidence["model"]["name"], "audience": candidate["audience"],
             "viewer_question": response["viewer_question"], "content_promise": response["content_promise"],
             "essential_nuance": candidate["essential_nuance"], "selection_reason": response["selection_reason"],
             "benchmark": {"references": references, "registry_sha256": fingerprint(registry)},
             "content_evidence": content_evidence, "concepts": concepts,
             "preferred_concept_id": "concept-"+str(response["preferred_index"]+1), "generation_evidence": evidence,
             "citation_alignment": {"assignments": alignment["assignments"], "evidence": alignment_proof},
             "concept_plan": {"plan": concept_plan, "evidence": plan_evidence}}
    brief['metadata_mode']=response['metadata_mode']
    brief['review_feedback']=job['payload'].get('review_feedback')
    bundle = create_bundle(brief, episode, candidate, asset, directory / "thumbnails", config, now=now)
    images = [{"path": p["path"], "sha256": p["sha256"], "concept_id": variant["concept_id"], "kind": p["kind"]}
              for variant in bundle["variants"] for p in variant["previews"]]
    individual = []
    for concept in concepts:
        individual.append(review_images(model, "thumbnail_review", [i for i in images if i["concept_id"] == concept["concept_id"]],
            {"target_concept": {k: concept[k] for k in ("concept_id", "video_title", "thumbnail_text", "angle", "hypothesis", "image", "evidence_ids")},
             "essential_nuance": candidate["essential_nuance"],
             "content_evidence": [{k: p[k] for k in ("evidence_id", "quote", "start_seconds", "end_seconds")} for p in content_evidence if p["evidence_id"] in concept["evidence_ids"]],
             "identity": config["identity"],
             "asset_sha256": asset["sha256"], "source_image_rights": "user_supplied_master"},
            ("faithfulness", "french_language", "title_image_complementarity", "mobile_readability", "composition", "identity_and_rights")))
    individual.append(review_images(model, "thumbnail_comparison", [next(a for a in bundle["artifacts"] if a["kind"] == "comparison")],
        {"concepts": [{k: c[k] for k in ("concept_id", "video_title", "thumbnail_text", "angle", "hypothesis", "evidence_ids")} for c in concepts],
         "content_evidence": content_evidence, "kept_speech": spoken_units, "essential_nuance": candidate["essential_nuance"],
         "viewer_question": response["viewer_question"], "content_promise": response["content_promise"],
         "platform_texts": response["platform_texts"]}, ("distinct_hypotheses", "brief_fidelity", "french_language")))
    review = {"passed": all(r["passed"] for r in individual), "batches": [b for r in individual for b in r["batches"]],
              "scope": "each_concept_and_its_own_spoken_evidence", "human_listening": False, "continuous_viewing": False}
    bundle["local_review"] = {**review, "content_digest": bundle_digest(bundle), "human_review": False}
    bundle["review_status"] = "local_passed" if review["passed"] else "local_failed"
    write_json(Path(bundle["receipt_path"]), bundle)
    store.put("thumbnail_bundle", bundle["bundle_id"], bundle, episode_id=episode["episode_id"], now=now)
    if not review["passed"]:
        if attempt+1 < options["maximum_model_attempts"]:
            issues = [{"criterion": name, "reason": value["reason"]} for batch in review["batches"]
                      for name, value in batch["checks"].items() if not value["passed"]]
            return thumbnails(store, episode, config, job, now=now, attempt=attempt+1, feedback=issues)
        raise LocalModelError("local_packaging_quality_failed")
    assert_local_asset(episode, asset)
    selected = bundle["variants"][response["preferred_index"]]
    with store.transaction():
        if _episode(store, job, config) is None:
            return {"status": "superseded"}
        packs=[p for p in store.publications(episode['episode_id']) if p['asset_id']==asset['asset_id']]
        if any(not p.get('local_only') or p.get('remote_id') or p.get('scheduled_at') for p in packs):
            raise LocalModelError('local_packaging_remote_intent_refused')
        for pack in packs:ensure_packaging_unlocked(pack['id'],store.records('experiment'))
        supersede_bundles(store, asset, bundle["bundle_id"], now=now)
        for pack in packs:
            pack.update(title=selected["title"], text=punctuation(response["platform_texts"][pack["platform"]]),
                        cover=selected["thumbnail"]["path"], cover_sha256=selected["thumbnail"]["sha256"],
                        thumbnail_bundle=bundle, variants=bundle["variants"], local_only=True, status="local_ready",
                        qa_status="local_passed", packaging_status="local_passed", scheduled_at=None, blocked_reason=None,
                        local_run_key=job["payload"]["local_run_key"], local_packaging_version=PACKAGING_VERSION)
            pack["local_packaging_review"] = {"revision": revision(pack), "bundle_digest": bundle["content_digest"],
                                               "scope": "local_automatic", "human_review": False}
            from .local_exports import export_pack
            pack = export_pack(pack, asset, episode, directory / "packs")
            store.put("packaging", pack["id"], pack, episode_id=episode["episode_id"], now=now)
            store.save_publication(pack, now=now)
    return {"bundle_id": bundle["bundle_id"], "packs": len(packs), "status": "local_passed"}


def calendar(store, episode: dict, config: dict, job: dict, *, now=None) -> dict:
    from .packaging import revision
    from .scheduler import local_slots
    from .thumbnails import validate_bundle
    from .local_exports import export_pack, verify_pack
    now = instant(now or utcnow())
    key = job["payload"]["local_run_key"]
    rows, blocked = [], []
    for pack in store.publications(episode["episode_id"]):
        if pack.get("local_run_key") != key or pack.get("status") in {"archived", "cancelled"}:
            continue
        try:
            asset = store.get("asset", pack["asset_id"])
            candidate = store.get("candidate", pack["segment_id"])
            if (pack["status"] != "local_ready" or pack.get("local_packaging_version") != PACKAGING_VERSION or candidate.get("decision") != "retained"
                    or candidate.get("local_run_key") != key):
                raise LocalModelError("local_content_not_ready")
            assert_local_asset(episode, asset)
            verify_pack(pack, asset)
            verify_review_files(candidate["local_editorial_review"])
            verify_evidence_files(candidate.get("boundary_refinement", {}))
            verify_evidence_files(candidate.get("local_edit_plan", {}))
            bundle = pack["thumbnail_bundle"]
            validate_bundle(bundle, asset=asset)
            brief = load_json(Path(bundle["brief_path"]))
            if brief.get('metadata_mode')!='source_bound_v1':
                raise LocalModelError('local_packaging_metadata_not_source_bound')
            kept_text=' '.join(r['text'] for r in _segments(episode) if candidate['start_seconds']<=r['start'] and r['end']<=candidate['end_seconds'])
            for concept in brief['concepts']:validate_editorial_question(concept['editorial_question'],kept_text)
            for field in ("generation_evidence", "concept_plan", "citation_alignment", "concepts"):
                verify_evidence_files(brief[field])
            if bundle.get('independent_local_review'):
                from .local_review import assert_review
                assert_review(bundle,asset)
            else:
                verify_review_files(bundle["local_review"])
                if not bundle['local_review']['passed'] or bundle['local_review']['content_digest']!=bundle['content_digest']:
                    raise LocalModelError('local_packaging_review_changed')
            if (pack["local_packaging_review"]["revision"] != revision(pack)
                    or pack['local_packaging_review']['bundle_digest']!=bundle['content_digest']):
                raise LocalModelError("local_packaging_review_changed")
            rows.append(pack)
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            blocked.append({"publication_id": pack["id"], "reason": str(error) if isinstance(error, LocalModelError) else type(error).__name__})
    missing = [name for name in ("planned_publication_at", "next_filming_at") if not episode.get(name)]
    planned, surplus = [], []
    counts, times = {}, {}
    if not missing:
        start = max(now, instant(episode.get("available_at") or episode["planned_publication_at"]))
        finish = instant(episode["next_filming_at"])-timedelta(minutes=config["schedule"]["processing_margin_minutes"])
        latest = finish-timedelta(minutes=config["schedule"]["connector_latency_minutes"])
        for pack in rows:
            account = (pack["platform"], pack["account_id"])
            selected = None
            for slot in local_slots(start, latest, config["schedule"]["slots_local"]):
                day = slot.astimezone(PARIS).date().isoformat()
                if counts.get(account+(day,), 0) >= config["schedule"]["maximum_per_day_per_account"]:
                    continue
                if any(abs((slot-previous).total_seconds()) < config["schedule"]["minimum_spacing_minutes"]*60 for previous in times.get(account, [])):
                    continue
                selected = slot
                counts[account+(day,)] = counts.get(account+(day,), 0)+1
                times.setdefault(account, []).append(slot)
                break
            item = {"publication_id": pack["id"], "platform": pack["platform"], "account_id": pack["account_id"],
                    "title": pack["title"], "asset_id": pack["asset_id"], "pack_path": pack["pack_path"],
                    "proposed_at": iso(selected) if selected else None, "status": "planned_local" if selected else "outside_remaining_window"}
            exported = export_pack(pack, store.get("asset",pack["asset_id"]), episode, _directory(store,episode) / "packs",
                                   proposed_at=item["proposed_at"], valid_until=iso(latest))
            store.save_publication(exported, now=now)
            store.put("packaging",pack["id"],exported,episode_id=episode["episode_id"],now=now)
            item["pack_path"] = exported["pack_path"]
            (planned if selected else surplus).append(item)
    errors = [{"kind": j["kind"], "job_id": j["id"], "reason": j["last_error"]} for j in store.jobs()
              if j["payload"].get("local_run_key") == key and j["kind"] != "local_calendar" and j["status"] in {"blocked", "failed"}]
    selection_pending = [{"segment_id": c["segment_id"], "reason": "local_editorial_review_failed"}
                         for c in store.records("candidate", episode["episode_id"]) if c.get("local_run_key") == key and c["decision"] == "needs_review"]
    result = {"episode_id": episode["episode_id"], "local_run_key": key, "revision": episode["revision"],
              "generated_at": iso(now), "local_only": True, "valid_for_publication": False,
              "conditional_on_episode_availability": episode.get("availability") != "available",
              "requires_destination": not bool(episode.get("full_episode_url")), "missing": missing,
              "assumptions": episode.get("local_calendar_assumptions", []),
              "planned": planned, "surplus": surplus, "blocked": blocked, "stage_errors": errors, "selection_needs_review": selection_pending,
              "ready_packs": len(rows), "timezone": "Europe/Paris"}
    run = store.get("local_run", key)
    run["status"] = "partial" if rows and (missing or errors or blocked or surplus or selection_pending) else "blocked" if missing or errors or blocked or selection_pending else "completed"
    result["status"] = run["status"]
    report = store.directory / "reports" / (episode["episode_id"]+"-local-"+job["payload"].get("calendar_revision", key)[:24]+".json")
    result["report_path"] = str(report)
    write_json(report, result)
    markdown = ["# Calendrier local : "+episode["title"], "", "Prévision locale uniquement. Aucun envoi ni programmation sur les réseaux.",
                "La disponibilité de l'émission et les accès aux comptes restent à confirmer.", "",
                *[f"- {p['proposed_at']} : {p['platform']} / {p['title']}" for p in planned], "",
                "Données complètes : "+report.name]
    report.with_suffix(".md").write_text("\n".join(markdown)+"\n", encoding="utf-8")
    with store.transaction():
        store.put("local_calendar", episode["episode_id"], result, episode_id=episode["episode_id"], now=now)
        store.put("local_run", key, {**run, "finished_at": iso(now), "report_path": str(report)}, episode_id=episode["episode_id"], now=now)
        store.event("local_calendar_prepared", episode["episode_id"], {"planned": len(planned), "status": result["status"], "local_only": True}, now=now)
    return result


def execute(store, config: dict, job: dict, *, now=None) -> dict:
    return measured(job["kind"])(_execute)(store, config, job["episode_id"], job, now=now)


def _execute(store, config: dict, episode_id: str, job: dict, *, now=None) -> dict:
    episode = _episode(store, job, config)
    if episode is None:
        return {"status": "superseded"}
    methods = {"local_transcribe": transcription, "local_analyze": selection, "local_recheck": recheck, "local_render": render_local,
               "local_quality": quality, "local_thumbnails": thumbnails, "local_calendar": calendar}
    store.event("local_stage_started", job["id"], {"kind": job["kind"], "local_only": True}, now=now)
    store._local_inference_scope = True
    store._local_inference_client = None
    try:
        result = methods[job["kind"]](store, episode, config, job, now=now)
    finally:
        client = store._local_inference_client
        store._local_inference_scope = False
        store._local_inference_client = None
        if client and hasattr(client, "close"):
            try:
                client.close()
            except LocalModelError as error:
                # The one-minute keep-alive is the bounded fallback on crash or
                # failed cleanup. Do not replace the original stage outcome.
                store.event("local_model_release_delayed", job["id"], {"code": str(error)}, now=now)
    store.event("local_stage_completed", job["id"], {"kind": job["kind"], "result": result}, now=now)
    return result
