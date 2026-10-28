"""Read-only operational diagnostics. No media hashing or network calls on refresh."""
from __future__ import annotations

from collections import Counter
import json

from .contracts import instant, iso, utcnow


REMEDIES = {
    "quality_review_required": "Regarder et écouter le rendu, puis consigner la revue audiovisuelle et éditoriale.",
    "thumbnail_packaging_review_required": "Préparer les trois concepts titre/image et faire relire leurs aperçus.",
    "account_not_authorized": "Vérifier le compte prévu dans la configuration de simulation.",
    "source_changed_after_dispatch": "Comparer le nouveau master à la source précédente et réconcilier la révision.",
    "candidate_not_selected": "Vérifier la décision éditoriale avant de préparer un nouveau calendrier.",
    "editorial_selection_not_retained": "Ce passage a été retiré. Revoir la sélection avant tout nouveau calendrier.",
    "editorial_revision_changed": "Reprendre l'analyse et la sélection pour la nouvelle révision de l'épisode.",
    "editorial_analysis_revision_changed": "Reprendre les rendus depuis la sélection correspondant à l'analyse actuelle.",
    "daily_limit_replan_required": "Replanifier ce contenu dans un créneau admissible avant la fin de la fenêtre.",
    "missed_slot_replan_required": "Le créneau est passé. Replanifier dans la fenêtre restante, sans rattrapage en rafale.",
}


def worker_health(heartbeat, *, now=None, stale_after_seconds=180):
    now = instant(now or utcnow())
    result = {"status": "missing", "at": None, "age_seconds": None}
    if not heartbeat:
        return result
    if not isinstance(heartbeat, dict):
        result["status"] = "invalid"
        return result
    result["at"] = heartbeat.get("at")
    if heartbeat.get("clock") == "controlled_simulation":
        result["status"] = "simulation"
        return result
    try:
        if not isinstance(heartbeat.get("at"), str):
            raise ValueError("Missing timestamp")
        age = (now-instant(heartbeat["at"])).total_seconds()
    except (KeyError, TypeError, ValueError):
        result["status"] = "invalid"
        return result
    result.update(age_seconds=max(0, round(age)), status=("clock_skew" if age < -30 else "stale" if age > stale_after_seconds else "healthy"))
    return result


def enrich(store, state, config, *, now=None):
    """Enrich a status snapshot without implying readiness from counts alone."""
    now = instant(now or utcnow())
    episodes = state["episodes"]
    episode_ids = {e["episode_id"] for e in episodes}
    result = dict(state)
    result["generated_at"] = iso(now)
    result["context"] = {
        "state_directory": str(store.directory), "database": str(store.path),
        "synthetic_episode_count": sum(bool(e.get("synthetic")) for e in episodes),
        "real_episode_count": sum(not e.get("synthetic", False) for e in episodes),
    }
    counts = Counter(j["status"] for j in state["jobs"])
    result["health"] = {
        "worker": worker_health(state.get("heartbeat"), now=now),
        "queued_jobs": counts["queued"], "running_jobs": counts["running"],
        "failed_jobs": counts["failed"]+counts["blocked"],
    }
    # Older window payloads omit their episode; the record column is authoritative.
    result["windows"] = [dict(json.loads(r["data"]), episode_id=r["episode_id"])
                         for r in store.db.execute("SELECT episode_id,data FROM records WHERE kind='window'")
                         if r["episode_id"] in episode_ids]
    attention = []
    for p in state["publications"]:
        if p["status"] not in {"blocked", "unknown", "error"}:
            continue
        unknown = p["status"] == "unknown"
        reason = p.get("blocked_reason") or p["status"]
        attention.append({"kind": "publication", "entity_id": p["id"], "episode_id": p["episode_id"],
                          "title": p.get("title") or p["id"], "reason": reason,
                          "severity": "critical" if unknown else "warning",
                          "next_action": "Vérifier le reçu et réconcilier le résultat avant toute reprise." if unknown else REMEDIES.get(reason, "Lire le motif et corriger la condition manquante avant de replanifier.")})
    for asset in state["assets"]:
        if asset.get("qa_status") == "passed":
            continue
        attention.append({"kind": "asset", "entity_id": asset["asset_id"], "episode_id": asset.get("episode_id"),
                          "title": "Revue du rendu "+asset.get("format", ""), "reason": asset.get("qa_status", "needs_review"),
                          "severity": "warning", "next_action": REMEDIES["quality_review_required"]})
    for job in state["jobs"]:
        if job["status"] not in {"failed", "blocked", "unknown"}:
            continue
        attention.append({"kind": "job", "entity_id": job["id"], "episode_id": job.get("episode_id"),
                          "title": "Traitement "+job["kind"], "reason": job.get("last_error") or job["status"],
                          "severity": "critical" if job["status"] == "unknown" else "warning",
                          "next_action": "Réconcilier le résultat incertain." if job["status"] == "unknown" else "Corriger la cause, puis reprendre ce traitement dans l'activité."})
    result["attention"] = sorted(attention, key=lambda a: a["severity"] != "critical")
    # Scope history to entities belonging to the selected episodes, while retaining
    # global worker/queue events. LIMIT happens after SQL filtering, not in Python.
    ids = sorted(episode_ids)
    marks = ",".join("?" for _ in ids) or "NULL"
    query = f"""SELECT sequence,kind,entity_id,data,created_at FROM events
        WHERE entity_id IS NULL OR entity_id IN ({marks})
        OR entity_id IN (SELECT id FROM records WHERE episode_id IN ({marks}))
        OR entity_id IN (SELECT id FROM publications WHERE episode_id IN ({marks}))
        OR entity_id IN (SELECT id FROM jobs WHERE episode_id IN ({marks}))
        ORDER BY sequence DESC LIMIT 50"""
    result["recent_events"] = [{**dict(r), "data": json.loads(r["data"])} for r in store.db.execute(query, ids*4)]
    return result
