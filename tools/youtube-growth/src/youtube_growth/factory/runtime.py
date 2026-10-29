"""Persistent local workers. No model invocation or social transport is implicit."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta
import json
from pathlib import Path
import threading
import time

from .contracts import ROOT, digest, episode_blockers, instant, iso, load_json, utcnow, validate_episode
from .store import Store
from .efficiency import measured, summarize_runs
from . import scheduler


def episode_record_id(store: Store, kind: str, identity: str, episode_id: str) -> str:
    """Keep existing IDs, but never overwrite another episode's content record."""
    existing = store.get(kind, identity)
    if existing and existing.get("episode_id") != episode_id:
        return identity+"-"+digest({"episode_id": episode_id})[:16]
    return identity


def render_revision(candidate: dict, episode: dict, analysis: dict) -> str:
    return digest({"candidate": candidate, "episode_title": episode["title"], "destination": episode.get("full_episode_url"),
                   "source": episode["source_sha256"], "transcript": analysis.get("transcript_sha256")})


def ingest(store: Store, manifest: Path, *, now=None, verify_source=False) -> dict:
    from .media import fingerprint, probe
    manifest = manifest.resolve(strict=True)
    episode = validate_episode(load_json(manifest), base=manifest.parent)
    source = Path(episode["source"])
    before = source.stat()
    previous = store.get("episode", episode["episode_id"])
    expected = episode.get("source_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("Signal de fin requis : source_sha256 doit être écrit dans le manifeste après la copie.")
    stat = {"size": before.st_size, "mtime_ns": before.st_mtime_ns}
    cached = (previous and previous.get("source") == str(source) and previous.get("source_sha256") == expected and previous.get("source_stat") == stat)
    actual = previous["source_sha256"] if cached and not verify_source else fingerprint(source)
    after = source.stat()
    if expected != actual or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Fichier incomplet ou modifié pendant l'ingestion.")
    info = previous["source_probe"] if cached else probe(source)
    for field in ("transcript", "evidence"):
        episode[field+"_sha256"] = fingerprint(Path(episode[field])) if episode.get(field) and Path(episode[field]).is_file() else None
    episode.update(source_sha256=actual, source_probe=info, source_stat=stat, imported_from=str(manifest))
    changed_after_dispatch = previous and previous.get("source_sha256") != actual and any(p["status"] in {"published", "simulated", "sending", "unknown", "manual_confirmed"} for p in store.publications(episode["episode_id"]))
    if changed_after_dispatch or previous and previous.get("source_revision_requires_reconciliation"):
        episode["source_revision_requires_reconciliation"] = True
    episode["revision"] = digest(episode)
    identity = episode["episode_id"]
    with store.transaction():
        previous = store.get("episode", identity)
        if previous and previous.get("revision") == episode["revision"]:
            return {"episode_id": identity, "status": "duplicate_ignored"}
        editorial_changed = previous and any(previous.get(field) != episode.get(field) for field in
            ("source_sha256", "transcript_sha256", "evidence_sha256", "title", "full_episode_url"))
        if editorial_changed:
            # Published logical identities are preserved; new media never means a new post.
            for row in store.publications(identity):
                if row["status"] not in scheduler.TERMINAL:
                    row.update(status="blocked", blocked_reason="editorial_revision_changed", editorial_current=False, scheduled_at=None)
                    if previous["source_sha256"] != actual:
                        row["qa_status"] = "needs_review"
                    store.save_publication(row, now=now)
                    store.db.execute("UPDATE jobs SET status='blocked' WHERE kind='dispatch' AND json_extract(payload,'$.publication_id')=? AND status IN ('queued','failed')", (row["id"],))
        store.put("episode", identity, episode, episode_id=identity, now=now)
        store.put("episode_revision", identity+":"+episode["revision"], episode, episode_id=identity, now=now)
        if episode.get("local_autonomy") is not True:
            store.enqueue("process", identity, {"revision": episode["revision"]}, now=now)
        store.event("episode_ingested", identity, {"source_sha256": actual, "revision": episode["revision"], "blockers": episode_blockers(episode)}, now=now)
    return {"episode_id": identity, "status": "ingested", "blockers": episode_blockers(episode)}


def watch(store: Store, config: dict, *, now=None) -> dict:
    inbox = Path(config["inbox_directory"])
    if not inbox.is_absolute():
        inbox = ROOT / inbox
    inbox.mkdir(parents=True, exist_ok=True)
    receipts, errors, skipped = [], [], 0
    current = instant(now or utcnow())
    for path in sorted(inbox.glob("*.ready.json")):
        try:
            # Poll metadata cheaply, but periodically rehash the source. A watcher
            # cache is not proof that a media file still matches its review.
            snapshot = _input_snapshot(path)
            key = digest(str(path.resolve()))
            previous = store.get("watch_receipt", key)
            interval = config["runtime"].get("watch_verify_seconds", 3600)
            age = (current-instant(previous.get("source_verified_at", previous["verified_at"]))).total_seconds() if previous else None
            if (previous and previous["inputs"] == snapshot and
                    0 <= age < interval):
                skipped += 1
                continue
            verify_source = (not previous or not 0 <= age < interval or
                             previous["inputs"].get("source") != snapshot.get("source"))
            receipt = ingest(store, path, now=now, verify_source=verify_source)
            receipts.append(receipt)
            if _input_snapshot(path) == snapshot:
                source_verified = iso(current) if verify_source else previous.get("source_verified_at", previous["verified_at"])
                store.put("watch_receipt", key, {"inputs": snapshot, "verified_at": iso(current),
                                               "source_verified_at": source_verified}, now=now)
        except (OSError, ValueError, RuntimeError) as error:
            # The ready file stays in place and can be corrected; suppress unchanged errors.
            issue = {"manifest": str(path), "error_type": type(error).__name__}
            errors.append(issue)
            key = digest({"path": str(path), "stat": _file_signature(path), "error": str(error)})
            if not store.get("ingestion_error", key):
                store.put("ingestion_error", key, issue, now=now)
                store.event("ingestion_blocked", None, issue, now=now)
    return {"ingested": receipts, "errors": errors, "unchanged": skipped}


def _file_signature(path: Path):
    try:
        stat = path.stat()
    except OSError:
        return None
    return [stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_dev, stat.st_ino]


def _input_snapshot(manifest: Path):
    signatures = {"manifest": {"path": str(manifest.resolve()), "signature": _file_signature(manifest)}}
    value = load_json(manifest)
    for field in ("source", "transcript", "evidence"):
        if value.get(field):
            if not isinstance(value[field], str):
                raise ValueError("Chemin local invalide dans le manifeste.")
            path = Path(value[field])
            path = (manifest.parent / path).resolve()
            signatures[field] = {"path": str(path), "signature": _file_signature(path)}
    return signatures


def idle_delay(store: Store, config: dict, *, idle_count: int, interval: float, now=None) -> float:
    """Back off an empty worker without sleeping past known due work or closure."""
    current = instant(now or utcnow())
    delay = min(interval * 2 ** min(max(idle_count-1, 0), 10), config["runtime"].get("idle_max_seconds", 60))
    paused_filter = " AND kind IN ('collect','report')" if store.setting("paused", False) else ""
    deadlines = []
    for column, predicate in (("due_at", "status='queued' AND attempts<?"), ("lease_until", "status='running'")):
        params = (config["runtime"]["maximum_attempts"],) if column == "due_at" else ()
        row = store.db.execute(f"SELECT MIN({column}) FROM jobs WHERE {predicate}"+paused_filter, params).fetchone()
        if row[0]:
            deadlines.append(instant(row[0]))
    for name, hours in (("last_collection_at", config["metrics"]["interval_hours"]),
                        ("last_report_at", config["metrics"]["report_interval_hours"])):
        last = store.setting(name)
        if last and instant(last)+timedelta(hours=hours) > current:
            deadlines.append(instant(last)+timedelta(hours=hours))
    for episode in store.records("episode"):
        if episode.get("next_filming_at"):
            deadline = instant(episode["next_filming_at"])-timedelta(minutes=config["schedule"]["processing_margin_minutes"])
            if deadline > current:
                deadlines.append(deadline)
    for deadline in deadlines:
        delay = min(delay, max(0.1, (deadline-current).total_seconds()))
    return delay


@measured("process")
def process(store: Store, config: dict, episode_id: str, *, now=None) -> dict:
    from .media import analyze
    episode = store.get("episode", episode_id)
    if not episode:
        raise ValueError("Épisode inconnu.")
    output = store.directory / "episodes" / episode_id
    result = analyze(Path(episode["source"]), Path(episode["transcript"]) if episode.get("transcript") and Path(episode["transcript"]).is_file() else None,
                     output / "analysis", evidence=Path(episode["evidence"]) if episode.get("evidence") and Path(episode["evidence"]).is_file() else None)
    store.put("analysis", episode_id, result, episode_id=episode_id, now=now)
    current_ids = set()
    for candidate in result["candidates"]:
        identity = episode_record_id(store, "candidate", candidate["segment_id"], episode_id)
        candidate["segment_id"] = identity
        current_ids.add(identity)
        candidate.update(episode_id=episode_id, source_sha256=episode["source_sha256"], episode_revision=episode.get("revision"))
        store.put("candidate", identity, candidate, episode_id=episode_id, now=now)
        if candidate.get("decision") == "retained":
            format_name = candidate.get("format", "vertical" if candidate["end_seconds"]-candidate["start_seconds"] < 180 else "horizontal")
            store.enqueue("render", episode_id, {"segment_id": identity, "format": format_name,
                          "revision": render_revision(candidate, episode, result)}, now=now)
    for old in store.records("candidate", episode_id):
        if old["segment_id"] not in current_ids:
            old.update(decision="archived", rejection_reason="removed_from_current_editorial_evidence")
            store.put("candidate", old["segment_id"], old, episode_id=episode_id, now=now)
    # Removing a selection must revoke its existing packs as well as its render jobs.
    retained = {c["segment_id"] for c in result["candidates"] if c.get("decision") == "retained"}
    for row in store.publications(episode_id):
        if row.get("segment_id") not in retained and row["status"] not in scheduler.TERMINAL:
            row.update(status="blocked", editorial_current=False, blocked_reason="editorial_selection_not_retained", scheduled_at=None)
            store.save_publication(row, now=now)
            store.db.execute("UPDATE jobs SET status='blocked' WHERE kind='dispatch' AND json_extract(payload,'$.publication_id')=? AND status IN ('queued','failed')", (row["id"],))
    store.event("analysis_completed", episode_id, {"candidates": len(result["candidates"]), "blockers": result.get("blockers", [])}, now=now)
    if config.get("generation", {}).get("auto_editorial"):
        from .editorial_runtime import discover, assess
        result["discovery"] = discover(store, config, episode_id, use_model=True, now=now)
        result["editorial"] = assess(store, config, episode_id=episode_id, use_model=True, now=now)
    return result


@measured("render")
def render_candidate(store: Store, config: dict, episode_id: str, segment_id: str, format_name: str, *, now=None) -> dict:
    from .media import render
    from .packaging import prepare
    from .analytics import ensure_packaging_unlocked
    episode, candidate = store.get("episode", episode_id), store.get("candidate", segment_id)
    if not episode or not candidate or candidate.get("episode_id") != episode_id or candidate.get("decision") != "retained":
        raise ValueError("Candidat retenu et lié à l'épisode requis.")
    opportunity = store.get("opportunity", segment_id)
    from .editorial import assert_compatible
    assert_compatible(opportunity, candidate, now=now)
    if episode.get("revision") and candidate.get("episode_revision") != episode["revision"]:
        raise ValueError("editorial_analysis_revision_changed")
    for existing in store.publications(episode_id):
        if existing.get("segment_id") == segment_id:
            ensure_packaging_unlocked(existing["id"], store.records("experiment"))
    asset = render(Path(episode["source"]), candidate, store.directory / "episodes" / episode_id / "renders",
                   format=format_name, transcript=Path(episode["transcript"]) if episode.get("transcript") else None,
                   fixture=episode.get("synthetic", False),alignment_options=config.get('autonomy') if candidate.get('local_only') else None)
    asset["asset_id"] = episode_record_id(store, "asset", asset["asset_id"], episode_id)
    asset.update(episode_id=episode_id, segment_id=segment_id, qa_status="needs_review", synthetic=episode.get("synthetic", False))
    previous = store.get("asset", asset["asset_id"])
    if previous and previous.get("sha256") == asset["sha256"]:
        asset["qa_status"] = previous.get("qa_status", "needs_review")
        asset["review"] = previous.get("review")
    store.put("asset", asset["asset_id"], asset, episode_id=episode_id, now=now)
    for pack in prepare(episode, candidate, asset, config, store.directory / "episodes" / episode_id / "packs"):
        previous_pack = store.publication(pack["id"])
        if previous_pack:
            ensure_packaging_unlocked(pack["id"], store.records("experiment"))
            if previous_pack["status"] in scheduler.TERMINAL:
                replacing_local = (episode.get('local_autonomy') and candidate.get('local_only')
                    and previous_pack.get('local_only') and previous_pack['status']=='archived'
                    and not previous_pack.get('remote_id') and not previous_pack.get('scheduled_at'))
                if not replacing_local:continue
            if previous_pack["asset_sha256"] != asset["sha256"]:
                pack.update(status="blocked", blocked_reason="asset_revision_requires_review")
            from .packaging import revision
            if previous_pack.get("thumbnail_base_revision") == revision(pack) and previous_pack["asset_sha256"] == asset["sha256"]:
                for field in ("thumbnail_base_revision", "thumbnail_bundle", "title", "variants", "cover", "cover_sha256", "packaging_review", "packaging_status", "pack_path"):
                    if field in previous_pack:
                        pack[field] = previous_pack[field]
        store.put("packaging", pack["id"], pack, episode_id=episode_id, now=now)
        store.save_publication(pack, now=now)
    store.event("asset_rendered", asset["asset_id"], {"sha256": asset["sha256"], "review": asset["qa_status"]}, now=now)
    return asset


def prepare_thumbnails(store: Store, config: dict, publication_id: str, brief_path: Path, *, now=None):
    from .analytics import ensure_packaging_unlocked
    from .thumbnails import create_bundle
    from .packaging import revision
    row = store.publication(publication_id)
    if not row or row["platform"] != "youtube" or row["status"] in scheduler.TERMINAL:
        raise ValueError("Publication YouTube locale non envoyée requise.")
    scheduler.assert_editorial_current(store, row)
    ensure_packaging_unlocked(publication_id, store.records("experiment"))
    episode, asset, candidate = store.get("episode", row["episode_id"]), store.get("asset", row["asset_id"]), store.get("candidate", row["segment_id"])
    if not asset or asset["format"] != "horizontal" or not candidate:
        raise ValueError("Un extrait horizontal et sa sélection sont requis.")
    brief = load_json(brief_path.resolve(strict=True))
    for concept in brief.get("concepts", []):
        image = concept.get("image", {})
        if image.get("path") and not Path(image["path"]).is_absolute():
            image["path"] = str((brief_path.resolve().parent / image["path"]).resolve())
    bundle = create_bundle(brief, episode, candidate, asset, store.directory / "episodes" / row["episode_id"] / "thumbnails", config, now=now)
    selected = next(v for v in bundle["variants"] if v["concept_id"] == bundle["selected_concept_id"])
    row.setdefault("thumbnail_base_revision", revision(row))
    row.update(thumbnail_required=True, thumbnail_bundle=bundle, title=selected["title"], cover=selected["thumbnail"]["path"],
               cover_sha256=selected["thumbnail"]["sha256"], variants=bundle["variants"], packaging_status="needs_thumbnail_review",
               packaging_review=None, status="blocked", blocked_reason="thumbnail_packaging_review_required", scheduled_at=None)
    directory = store.directory / "episodes" / row["episode_id"] / "packs" / "youtube" / row["id"] / revision(row)[:20]
    directory.mkdir(parents=True, exist_ok=True)
    row["pack_path"] = str(directory / "pack.json")
    (directory / "pack.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    (directory / "texte.txt").write_text(row["text"]+"\n\n"+row["cta"]+"\n", encoding="utf-8")
    store.put("thumbnail_bundle", bundle["bundle_id"], bundle, episode_id=row["episode_id"], now=now)
    store.put("packaging", row["id"], row, episode_id=row["episode_id"], now=now)
    store.save_publication(row, now=now)
    store.event("thumbnail_concepts_prepared", row["id"], {"bundle_id": bundle["bundle_id"], "revision": revision(row)}, now=now)
    return row


def review_thumbnails(store: Store, publication_id: str, *, reviewer: str, evidence: str, checks: list[str], now=None):
    from .analytics import ensure_packaging_unlocked
    from .thumbnails import review_bundle
    from .packaging import revision, assert_reviewed
    row = store.publication(publication_id)
    if not row or row["status"] in scheduler.TERMINAL or not row.get("thumbnail_bundle"):
        raise ValueError("Concepts de miniature locaux à relire requis.")
    scheduler.assert_editorial_current(store, row)
    ensure_packaging_unlocked(publication_id, store.records("experiment"))
    bundle = review_bundle(row["thumbnail_bundle"], reviewer=reviewer, evidence=evidence, checks=checks, now=now)
    row.update(thumbnail_bundle=bundle, packaging_status="passed")
    row["packaging_review"] = {"reviewer": reviewer, "evidence": evidence, "revision": revision(row), "reviewed_at": iso(now or utcnow())}
    assert_reviewed(row, store.get("asset", row["asset_id"]))
    row.update(status="ready" if row.get("qa_status") == "passed" else "blocked", blocked_reason=None if row.get("qa_status") == "passed" else "quality_review_required")
    Path(bundle["receipt_path"]).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(row["pack_path"]).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    store.put("thumbnail_bundle", bundle["bundle_id"], bundle, episode_id=row["episode_id"], now=now)
    store.put("packaging", row["id"], row, episode_id=row["episode_id"], now=now)
    store.save_publication(row, now=now)
    store.event("thumbnail_packaging_reviewed", row["id"], row["packaging_review"], now=now)
    return row


def review(store: Store, asset_id: str, *, evidence: str, reviewer: str, checks: list[str], now=None, fixture=False) -> dict:
    from .media import fingerprint
    asset = store.get("asset", asset_id)
    required = {"visual", "audio", "editorial", "subtitles"}
    if not asset or set(checks) != required or not evidence.strip() or not reviewer.strip():
        raise ValueError("Revue explicite visual/audio/editorial/subtitles, preuve et responsable requis.")
    if fixture and not asset.get("synthetic"):
        raise ValueError("Une revue fixture ne peut valider un média réel.")
    if fingerprint(Path(asset["path"])) != asset["sha256"] or asset["qa"].get("technical") != "passed":
        raise ValueError("Le média a changé ou ses contrôles techniques échouent.")
    asset.update(qa_status="passed", review={"asset_sha256": asset["sha256"], "reviewer": reviewer, "evidence": evidence,
                 "checks": checks, "reviewed_at": iso(now or utcnow()), "scope": "synthetic_fixture" if fixture else "operator_attestation"})
    store.put("asset", asset_id, asset, episode_id=asset["episode_id"], now=now)
    for row in store.publications(asset["episode_id"]):
        if row["asset_id"] == asset_id and row["asset_sha256"] == asset["sha256"] and row["status"] not in scheduler.TERMINAL:
            row.update(qa_status="passed", status="ready", blocked_reason=None)
            if row.get("editorial_current") is False:
                row.update(status="blocked", blocked_reason="editorial_revision_changed")
            try:
                from .packaging import assert_reviewed
                assert_reviewed(row, asset)
            except (ValueError, OSError):
                row.update(status="blocked", blocked_reason="thumbnail_packaging_review_required")
            store.save_publication(row, now=now)
    store.event("asset_reviewed", asset_id, asset["review"], now=now)
    return asset


def dispatch(store: Store, config: dict, publication_id: str, *, now=None, connector=None) -> dict:
    from .connectors import build_connector
    controlled = now is not None
    now = instant(now or utcnow())
    with store.transaction():
        row = store.publication(publication_id)
        if not row:
            raise ValueError("Publication inconnue.")
        if row["status"] != "scheduled":
            raise ValueError("publication_already_reserved_or_not_scheduled")
        scheduler.assert_sendable(store, config, row, now=now)
        row.update(status="sending", publication_id=row["id"])
        store.save_publication(row, now=now)
        store.event("dispatch_intent", row["id"], {"simulation": True, "asset_sha256": row["asset_sha256"]}, now=now)
    connector = connector or build_connector(row["platform"], row["account_id"], config)
    # Re-read time, episode, file and queue after reservation immediately before send.
    send_time = now if controlled else utcnow()
    scheduler.assert_sendable(store, config, store.publication(publication_id), now=send_time)
    receipt = connector.dispatch(row)
    if receipt.get("status") != "simulated" or not str(receipt.get("remote_id", "")).startswith("sim:"):
        raise RuntimeError("Le connecteur n'a pas confirmé une simulation.")
    finished_at = now if controlled else utcnow()
    row.update(receipt, status="simulated", simulated_at=iso(finished_at), visibility="simulated")
    episode = store.get("episode", row["episode_id"])
    _, deadline = scheduler.window(episode, config)
    row["deadline_violation"] = instant(finished_at) >= deadline
    store.save_publication(row, now=finished_at)
    store.event("dispatch_simulated", row["id"], receipt, now=finished_at)
    return row


def collect(store: Store, config: dict, *, now=None, fixture=False) -> dict:
    from .analytics import validate_observation
    from .connectors import build_connector
    added = 0
    for row in store.publications():
        if row["status"] not in {"published", "simulated"} or row["platform"] == "linkedin":
            continue
        connector = build_connector(row["platform"], row["account_id"], config)
        for observation in connector.collect({**row, "publication_id": row["id"]}, fixture=fixture and row.get("synthetic", False), collected_at=now or utcnow()):
            validate_observation(observation)
            store.put("observation", observation["observation_id"], observation, episode_id=row["episode_id"], now=now)
            added += 1
    store.set_setting("last_collection_at", iso(now or utcnow()))
    store.event("metrics_collected", None, {"observations": added, "fixture": fixture}, now=now)
    return {"observations": added, "missing_metrics": "not_available" if not added else None, "synthetic_fixture": fixture}


def report(store: Store, *, episode_id=None, now=None, config=None) -> dict:
    from .analytics import summarize, conclude_experiment, budget_status
    from .contracts import load_config
    config = config or load_config()
    observations = store.records("observation", episode_id)
    result = {"generated_at": iso(now or utcnow()), "episode_id": episode_id, "mode": "simulation", "live_enabled": False,
              "publications": store.publications(episode_id), "metrics": summarize(observations),
              "experiments": [conclude_experiment(x, observations, now=now or utcnow()) for x in store.records("experiment", episode_id)],
              "costs": store.records("cost", episode_id), "decisions": store.records("decision", episode_id),
              "resources": summarize_runs(store.records("resource_run", episode_id)),
              "budget": budget_status(store.records("cost", episode_id), {"currency": config["budgets"]["currency"],
                         "episode_max": config["budgets"]["episode_limit"], "usable_content_count": sum(a.get("qa_status") == "passed" for a in store.records("asset", episode_id))}),
              "limits": ["Aucune performance réelle déduite de la simulation.", "Analyse audiovisuelle intégrale d'un épisode réel encore à valider."]}
    result["next_cycle"] = brief(store, config, episode_id=episode_id, now=now)
    output = store.directory / "reports"
    output.mkdir(exist_ok=True)
    name = (episode_id or "factory")+"-"+instant(now or utcnow()).strftime("%Y%m%dT%H%M%SZ")
    (output / (name+".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Bilan de la factory SANDBOX", "", "Mode simulation. Activation réelle désactivée.", "", f"Publications suivies : {len(result['publications'])}.", "", "| Plateforme | Titre | État |", "| --- | --- | --- |"]
    for p in result["publications"]:
        lines.append(f"| {p['platform']} | {p.get('title','').replace('|','/')} | {p['status']} |")
    lines += ["", f"Observations importées : {len(observations)}. Les mesures absentes restent absentes.", "", *result["limits"]]
    lines += ["", "## Consommation mesurée", "",
              "Les durées couvrent les appels d'analyse et de rendu instrumentés. Le CPU Python exclut FFmpeg.", "",
              "| Étape | Appels | Échecs | Durée cumulée (s) |", "| --- | ---: | ---: | ---: |"]
    for stage in result["resources"]["stages"]:
        lines.append(f"| {stage['stage']} | {stage['runs']} | {stage['failed']} | {stage['elapsed_seconds']} |")
    if not result["resources"]["stages"]:
        lines += ["", "Aucune durée enregistrée. Les anciens calculs ne sont pas estimés rétroactivement."]
    lines += ["", "## Préparer le prochain cycle", ""]
    learning = result["next_cycle"]["learning"]
    lines += [f"Observations réelles disponibles : {learning['observed_count']}. Observations synthétiques : {learning['synthetic_count']}.", ""]
    for action in learning["recommended_actions"]:
        reference = action.get("decision_id") or action.get("experiment_id") or action["action"]
        lines.append(f"- {reference} : {action['reason']}")
    if result["next_cycle"]["knowledge"]["review_required"]:
        lines += ["", "Des références demandent une nouvelle vérification ; consulter le registre dans le bilan JSON."]
    lines += ["", "Les faits, identifiants de preuve et références sont conservés dans le bilan JSON associé."]
    (output / (name+".md")).write_text("\n".join(lines)+"\n", encoding="utf-8")
    result["report_path"] = str(output / (name+".md"))
    store.set_setting("last_report_at", iso(now or utcnow()))
    return result


def brief(store: Store, config: dict, *, episode_id=None, now=None) -> dict:
    """Prepare the next review from current evidence, without models or network."""
    from .analytics import learning_brief, compare_content
    from .knowledge import knowledge_status
    current = instant(now or utcnow())
    episodes = [e for e in store.records("episode") if not episode_id or e["episode_id"] == episode_id]
    if episode_id and not episodes:
        raise ValueError("Épisode inconnu.")
    candidates = store.records("candidate", episode_id)
    return {"generated_at": iso(current), "episode_id": episode_id, "mode": "simulation",
            "positioning": config["identity"], "knowledge": knowledge_status(config, now=current),
            "learning": learning_brief(store.records("observation", episode_id),
                                       store.records("experiment", episode_id), store.records("decision"), now=current,
                                       decision_observations=store.records("observation")),
            "decisions_scope": "global_configuration",
            "comparable_performance": compare_content(store.records("observation", episode_id), store.records("performance_context"), now=current),
            "editorial_opportunities": store.records("opportunity", episode_id),
            "narrative_productions": store.records("narrative", episode_id),
            "resources": summarize_runs(store.records("resource_run", episode_id)),
            "readiness": [{"episode_id": e["episode_id"], "synthetic": e.get("synthetic", False),
                           "blockers": episode_blockers(e),
                           "candidates_to_review": sum(c.get("episode_id") == e["episode_id"] and c.get("decision") == "needs_review" for c in candidates),
                           "retained_candidates": sum(c.get("episode_id") == e["episode_id"] and c.get("decision") == "retained" for c in candidates)} for e in episodes],
            "policy": {"automatic_strategy_change": False, "editorial_quota": None,
                       "guide": "docs/factory/optimisation.md"}}


@contextmanager
def keep_lease(store: Store, job: dict, seconds: int, *, now=None):
    stop = threading.Event()
    def renew():
        with Store(store.directory) as heartbeat:
            while not stop.wait(max(1, seconds//3)):
                heartbeat.renew(job["id"], job["owner"], seconds=seconds, now=now or utcnow())
    thread = threading.Thread(target=renew, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=5)


def run_once(store: Store, config: dict, *, now=None) -> dict:
    from .connectors import ConnectorError
    from .autonomy import KINDS, advance, execute
    from .local_models import LocalModelError
    controlled = now is not None
    current = instant(now or utcnow())
    scheduler.close_cycles(store, config, now=current)
    watch_result = watch(store, config, now=current)
    advance(store, config, now=current)
    store.set_setting("heartbeat", {"at": iso(current), "mode": "simulation", "clock": "controlled_simulation" if controlled else "wall_clock", "pid": __import__("os").getpid()})
    # Collections and reports survive editorial closure and queue suspension.
    for name, interval, kind in (("last_collection_at", config["metrics"]["interval_hours"], "collect"),
                                  ("last_report_at", config["metrics"]["report_interval_hours"], "report")):
        last = store.setting(name)
        if not last or current-instant(last) >= timedelta(hours=interval):
            store.enqueue(kind, None, {}, key=kind+":"+str(int(current.timestamp()//(interval*3600))), now=current)
    job = store.reserve(now=current, lease_seconds=config["runtime"]["lease_seconds"], maximum_attempts=config["runtime"]["maximum_attempts"])
    if not job:
        return {"status": "idle", "watch": watch_result}
    try:
        with keep_lease(store, job, config["runtime"]["lease_seconds"], now=current if controlled else None):
            if job["kind"] in KINDS:
                result = execute(store, config, job, now=current if controlled else None)
            elif job["kind"] == "process":
                episode = store.get("episode", job["episode_id"])
                result = {"status": "superseded"} if episode["revision"] != job["payload"]["revision"] else process(store, config, job["episode_id"], now=current)
            elif job["kind"] == "render":
                candidate = store.get("candidate", job["payload"]["segment_id"])
                episode = store.get("episode", job["episode_id"])
                analysis = store.get("analysis", job["episode_id"]) or {}
                stale = job["payload"].get("revision") and (not candidate or not episode or
                    job["payload"]["revision"] != render_revision(candidate, episode, analysis))
                result = {"status": "superseded"} if stale else render_candidate(store, config, job["episode_id"], job["payload"]["segment_id"], job["payload"]["format"], now=current)
            elif job["kind"] == "dispatch":
                result = dispatch(store, config, job["payload"]["publication_id"], now=current if controlled else None)
            elif job["kind"] == "narrative":
                from .narrative import run
                from .media import fingerprint
                payload = job["payload"]
                if fingerprint(Path(payload["story_path"])) != payload["story_sha256"]:
                    result = {"status": "superseded"}
                else:
                    result = run(store, config, Path(payload["story_path"]), stage=payload["stage"],
                                 format_name=payload["format"], draft=payload["draft"], now=current)
                    if result.get("status") == "blocked":
                        raise ValueError("narrative_research_blocked")
            elif job["kind"] == "storytelling":
                from .storytelling import run
                row=store.get("storytelling",job["payload"]["story_id"])
                project=store.get("storytelling_project",job["payload"]["story_id"]) or {}
                if not row or row["revision"]!=job["payload"]["revision"] or (job["payload"].get("script_revision") and job["payload"]["script_revision"]!=project.get("script_revision")):
                    result={"status":"superseded"}
                else:
                    result=run(store,config,row["story_id"],now=current)
                    if result["status"] not in {"completed","superseded","revised"}:
                        store.finish(job,status="blocked",error="storytelling_"+result["status"])
                        return {"status":"blocked","job_id":job["id"],"kind":job["kind"],"project_status":result["status"]}
            elif job["kind"] == "collect":
                result = collect(store, config, now=current)
            elif job["kind"] == "report":
                result = report(store, now=current, config=config)
            else:
                raise ValueError("Type de job inconnu.")
        store.finish(job)
        return {"status": "completed", "job_id": job["id"], "kind": job["kind"]}
    except LocalModelError as error:
        from .autonomy import invalidate_calendar
        invalidate_calendar(store, job, str(error), now=current)
        retry = str(error) == "local_model_unavailable" and job["attempts"] < config["runtime"]["maximum_attempts"]
        state = "queued" if retry else "blocked"
        store.finish(job, status=state, error=str(error), due_at=current+timedelta(seconds=config["runtime"]["retry_seconds"]) if retry else None)
        store.event("local_stage_blocked", job["id"], {"code": str(error), "status": state}, now=current)
        return {"status": state, "job_id": job["id"], "error": str(error)}
    except ConnectorError as error:
        status = "unknown" if error.uncertain else "queued" if error.retryable and job["attempts"] < config["runtime"]["maximum_attempts"] else "blocked"
        retry_at = current+timedelta(seconds=error.retry_after_seconds or config["runtime"]["retry_seconds"])
        if job["kind"] == "dispatch":
            row = store.publication(job["payload"]["publication_id"])
            row.update(status="unknown" if error.uncertain else "scheduled" if status == "queued" else "blocked", blocked_reason=error.code)
            store.save_publication(row, now=current)
        store.finish(job, status=status, error=error.code, due_at=retry_at)
        store.event("job_error", job["id"], {"code": error.code, "status": status}, now=current)
        return {"status": status, "job_id": job["id"], "error": error.code}
    except Exception as error:
        # Arbitrary provider exception after intent is uncertain, never a blind retry.
        status = "blocked" if isinstance(error, ValueError) else "failed"
        # Only known local blocker codes are persisted; arbitrary error text may contain credentials.
        code = str(error) if isinstance(error, ValueError) and str(error) in scheduler.BLOCKER_CODES else type(error).__name__
        if job["kind"] == "dispatch":
            row = store.publication(job["payload"]["publication_id"])
            if row and row["status"] == "sending":
                row.update(status="unknown", blocked_reason="dispatch_interrupted_requires_reconciliation")
                store.save_publication(row, now=current)
                status = "unknown"
            elif row and row["status"] not in scheduler.TERMINAL:
                row.update(status="blocked", blocked_reason=code)
                store.save_publication(row, now=current)
        # No exception text from providers in persisted logs, which could contain credentials.
        store.finish(job, status=status, error=code)
        store.event("job_error", job["id"], {"error_type": code, "status": status}, now=current)
        return {"status": status, "job_id": job["id"], "error_type": code}


def status(store: Store, *, episode_id=None, platform=None) -> dict:
    return {"mode": "simulation", "live_enabled": False, "paused": store.setting("paused", False),
            "heartbeat": store.setting("heartbeat"), "episodes": [x for x in store.records("episode") if not episode_id or x["episode_id"] == episode_id],
            "candidates": store.records("candidate", episode_id), "assets": store.records("asset", episode_id),
            "opportunities": store.records("opportunity", episode_id), "proposals": store.records("proposal", episode_id),
            "narratives": store.records("narrative", episode_id),
            "analyses": store.records("analysis", episode_id), "windows": store.records("window", episode_id),
            "thumbnail_bundles": store.records("thumbnail_bundle", episode_id),
            "local_runs": store.records("local_run", episode_id), "local_calendars": store.records("local_calendar", episode_id),
            "publications": store.publications(episode_id, platform), "jobs": [j for j in store.jobs() if not episode_id or j["episode_id"] == episode_id],
            "experiments": store.records("experiment", episode_id), "observations": store.records("observation", episode_id),
            "costs": store.records("cost", episode_id), "decisions": store.records("decision", episode_id),
            "resources": summarize_runs(store.records("resource_run", episode_id))}
