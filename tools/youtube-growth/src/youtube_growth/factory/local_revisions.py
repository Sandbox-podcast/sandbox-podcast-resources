"""Versioned, source-bound editorial repairs. Local media are never deleted."""
from __future__ import annotations

import copy
from pathlib import Path

from .contracts import digest, load_json, iso, utcnow
from .local_models import validate
from .local_quality import TEXT, object_schema
from .media import fingerprint


CHANGE = object_schema({"segment_id": TEXT, "action": {"enum": ["archive", "revise"]}, "reason": TEXT,
    "title": {"type": "string", "minLength": 1, "maxLength": 110}, "essential_nuance": TEXT, "context": TEXT, "rationale": TEXT,
    "start_seconds": {"type": "number", "minimum": 0}, "end_seconds": {"type": "number", "exclusiveMinimum": 0}})
CHANGE['properties']['caption_grouping_version']={'const':2}
CHANGE["required"] = ["segment_id", "action", "reason"]
PLAN = object_schema({"version": {"const": 1}, "episode_id": TEXT, "source_sha256": TEXT,
    "transcript_sha256": TEXT, "reviewer": TEXT, "scope": TEXT, "human_listening": {"const": False},
    "changes": {"type": "array", "minItems": 1, "maxItems": 100, "items": CHANGE}})


def apply_plan(store, config: dict, path: Path, *, now=None) -> dict:
    from .analytics import ensure_packaging_unlocked
    from .autonomy import _segments, payload, write_json, run_key, supersede_bundles
    plan = validate(load_json(path), PLAN)
    if not store.setting("paused", False):
        raise ValueError("Suspendre la file locale avant de corriger ses contenus.")
    if any(j["status"] == "running" and j["kind"].startswith("local_") for j in store.jobs()):
        raise ValueError("Attendre la fin du traitement local actif avant une correction.")
    episode = store.get("episode", plan["episode_id"])
    if (not episode or not episode.get("local_autonomy") or episode["source_sha256"] != plan["source_sha256"]
            or episode["transcript_sha256"] != plan["transcript_sha256"]
            or fingerprint(Path(episode["source"])) != plan["source_sha256"]
            or fingerprint(Path(episode["transcript"])) != plan["transcript_sha256"]):
        raise ValueError("Le plan ne correspond pas au master et à la transcription actuels.")
    if len({c["segment_id"] for c in plan["changes"]}) != len(plan["changes"]):
        raise ValueError("Une seule correction par passage dans un plan.")
    proof = {"path": str(path.resolve()), "sha256": fingerprint(path), "reviewer": plan["reviewer"], "scope": plan["scope"], "human_listening": False}
    plan_id = digest({"episode_id": episode["episode_id"], "plan_sha256": proof["sha256"]})
    previous = store.get("local_editorial_plan", plan_id)
    if previous:
        if fingerprint(Path(previous["receipt_path"])) != previous["receipt_sha256"]:
            raise ValueError("Le reçu du plan appliqué a changé.")
        return {**previous, "status": "already_applied"}
    rows = _segments(episode)
    changes = []
    for change in plan["changes"]:
        before = store.get("candidate", change["segment_id"])
        if (not before or before.get("episode_id") != episode["episode_id"] or not before.get("local_only")
                or before.get("local_run_key") != run_key(episode, config) or before.get("source_sha256") != episode["source_sha256"]):
            raise ValueError("Seuls les passages locaux de cet épisode sont modifiables.")
        packs = [p for p in store.publications(episode["episode_id"]) if p.get("segment_id") == before["segment_id"]]
        if any(not p.get("local_only") or p.get("remote_id") or p.get("scheduled_at") for p in packs):
            raise ValueError("Une intention distante interdit cette correction locale.")
        for pack in packs:
            ensure_packaging_unlocked(pack["id"], store.records("experiment"))
        candidate = copy.deepcopy(before)
        candidate.update(local_edit_plan=proof, local_editorial_revision=digest({"before": before, "change": change, "proof": proof}),
                         local_editorial_revision_reason=change["reason"])
        if change["action"] == "archive":
            candidate.update(decision="archived", rejection_reason=change["reason"])
        else:
            if ("start_seconds" in change) != ("end_seconds" in change):
                raise ValueError("Fournir les deux bornes du montage.")
            if "start_seconds" in change:
                start, end = change["start_seconds"], change["end_seconds"]
                if not 0 <= start < end <= episode["source_probe"]["duration_seconds"]:
                    raise ValueError("Bornes hors du master.")
                kept = [r for r in rows if r["end"] > start and r["start"] < end]
                if not kept:
                    raise ValueError("La coupe ne contient aucune parole connue.")
                start, end = kept[0]["start"], kept[-1]["end"]
                if not config["autonomy"]["minimum_segment_seconds"] <= end-start <= config["autonomy"]["maximum_segment_seconds"]:
                    raise ValueError("Durée révisée hors des limites.")
                candidate.update(start_seconds=start, end_seconds=end,
                                 cuts=[{"source_start_seconds": start, "source_end_seconds": end}])
            for name in ("title", "essential_nuance", "context", "rationale"):
                if name in change:
                    candidate[name] = change[name]
            if 'caption_grouping_version' in change:candidate['caption_grouping_version']=change['caption_grouping_version']
            candidate.update(decision="needs_review", local_editorial_review={"passed": False, "batches": [], "scope": "revision_awaiting_recheck"})
            candidate["previous_boundary_refinement"] = candidate.get("boundary_refinement")
            candidate["boundary_refinement"] = {"evidence": proof, "scope": "editorial_revision_requires_fresh_review"}
        changes.append((before, candidate, packs))
    identity = digest({"plan": proof, "before": [b for b, _, _ in changes]})
    receipt = store.directory / "editorial-revisions" / (identity+".json")
    if not receipt.exists():
        write_json(receipt, {"plan": plan, "evidence": proof, "before": [b for b, _, _ in changes], "created_at": iso(now or utcnow())})
    else:
        old_receipt = load_json(receipt)
        if old_receipt.get("plan") != plan or old_receipt.get("before") != [b for b, _, _ in changes]:
            raise ValueError("Reçu historique incompatible.")
    result = {"changes": len(changes), "receipt_path": str(receipt), "receipt_sha256": fingerprint(receipt), "local_only": True}
    with store.transaction():
        for before, candidate, packs in changes:
            assets = [a for a in store.records("asset", episode["episode_id"]) if a.get("segment_id") == candidate["segment_id"]]
            asset_ids = {a["asset_id"] for a in assets}
            active_assets=[a for a in assets if a.get('qa_status')!='superseded']
            active_asset_ids={a['asset_id'] for a in active_assets}
            for job in store.jobs():
                if (job["kind"].startswith("local_") and job["status"] in {"queued", "blocked", "failed"}
                        and (job["payload"].get("segment_id") == candidate["segment_id"] or job["payload"].get("asset_id") in asset_ids)):
                    store.db.execute("UPDATE jobs SET status='cancelled',last_error='superseded_by_editorial_revision' WHERE id=?", (job["id"],))
            same_cuts = (before["cuts"] == candidate["cuts"] and candidate["decision"] != "archived"
                         and before.get('caption_grouping_version')==candidate.get('caption_grouping_version'))
            for asset in active_assets:
                asset.update(qa_status="needs_review" if same_cuts else "superseded", local_editorial_revision=candidate["local_editorial_revision"])
                store.put("asset", asset["asset_id"], asset, episode_id=episode["episode_id"], now=now)
                supersede_bundles(store,asset,now=now)
            for pack in packs:
                if pack.get('status') in {'archived','cancelled'} or pack['asset_id'] not in active_asset_ids:continue
                pack.update(status="local_preparing" if same_cuts else "archived", scheduled_at=None,
                            qa_status="needs_review" if same_cuts else "superseded", packaging_status="needs_review",
                            blocked_reason="editorial_revision", title=candidate["title"])
                store.save_publication(pack, now=now)
            store.put("candidate", candidate["segment_id"], candidate, episode_id=episode["episode_id"], now=now)
            if candidate["decision"] != "archived":
                store.enqueue("local_recheck", episode["episode_id"], payload(episode, config, segment_id=candidate["segment_id"],
                              editorial_revision=candidate["local_editorial_revision"]), now=now)
        analysis = store.get("analysis", episode["episode_id"])
        if analysis:
            replacement = {c["segment_id"]: c for _, c, _ in changes}
            analysis["candidates"] = [replacement.get(c["segment_id"], c) for c in analysis["candidates"]]
            analysis.setdefault("editorial_revisions", []).append({"path": str(receipt), "sha256": fingerprint(receipt)})
            store.put("analysis", episode["episode_id"], analysis, episode_id=episode["episode_id"], now=now)
        store.event("local_editorial_revision_applied", episode["episode_id"], {"receipt": str(receipt), "changes": len(changes)}, now=now)
        store.put("local_editorial_plan", plan_id, result, episode_id=episode["episode_id"], now=now)
    return result
