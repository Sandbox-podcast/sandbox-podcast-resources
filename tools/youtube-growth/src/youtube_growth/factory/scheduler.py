"""Paris editorial windows, independent closure, and no late catch-up."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, time, timedelta

from .contracts import PARIS, UTC, episode_blockers, instant, iso, utcnow

TERMINAL = {"published", "simulated", "unknown", "sending", "cancelled", "expired", "archived", "manual_confirmed"}
BLOCKER_CODES = {"queue_paused", "publication_not_sendable", "editorial_revision_changed",
    "editorial_selection_not_retained", "publication_window_expired_or_not_started", "publication_not_due",
    "missed_slot_replan_required", "linkedin_manual_only", "account_not_authorized",
    "minimum_spacing_replan_required", "account_has_uncertain_dispatch", "daily_limit_replan_required",
    "asset_or_review_changed", "asset_file_changed", "thumbnail_concepts_required",
    "selected_title_or_thumbnail_changed", "selected_thumbnail_file_changed", "packaging_revision_requires_review"}


def assert_editorial_current(store, publication):
    if publication.get("editorial_current") is False:
        raise ValueError("editorial_revision_changed")
    candidate = store.get("candidate", publication["segment_id"]) if publication.get("segment_id") else None
    if publication.get("segment_id") and candidate is None:
        raise ValueError("editorial_selection_not_retained")
    if candidate and (candidate.get("decision") != "retained" or candidate.get("episode_id") != publication["episode_id"]):
        raise ValueError("editorial_selection_not_retained")


def window(episode: dict, config: dict) -> tuple[datetime, datetime]:
    blockers = episode_blockers(episode)
    if blockers:
        raise ValueError(", ".join(blockers))
    start = instant(episode["available_at"])
    end = instant(episode["next_filming_at"])-timedelta(minutes=config["schedule"]["processing_margin_minutes"])
    if start >= end:
        raise ValueError("empty_publication_window")
    return start, end


def local_slots(start: datetime, end: datetime, times: list[str]):
    """Skip nonexistent wall times. Emit an ambiguous time once, with its offset."""
    day, last = start.astimezone(PARIS).date(), end.astimezone(PARIS).date()
    while day <= last:
        for text in sorted(set(times)):
            naive = datetime.combine(day, time.fromisoformat(text))
            local = naive.replace(tzinfo=PARIS, fold=0)
            candidate = local.astimezone(UTC)
            if candidate.astimezone(PARIS).replace(tzinfo=None) != naive:
                continue
            if start <= candidate < end:
                yield candidate
        day += timedelta(days=1)


def plan(store, config: dict, episode_id: str, *, now=None) -> dict:
    now = instant(now or utcnow())
    episode = store.get("episode", episode_id)
    if not episode:
        raise ValueError("Épisode inconnu.")
    rows = store.publications(episode_id)
    try:
        start, end = window(episode, config)
    except ValueError as error:
        for row in rows:
            if row["status"] not in TERMINAL:
                row.update(status="blocked", blocked_reason=str(error), scheduled_at=None)
                store.save_publication(row, now=now)
        return {"episode_id": episode_id, "blocked": str(error), "scheduled": 0}
    latency = timedelta(minutes=config["schedule"]["connector_latency_minutes"])
    latest = end-latency
    bounds = {"start_at": iso(start), "finish_before": iso(end), "last_send_before": iso(latest), "timezone": "Europe/Paris"}
    # Reschedule unsent content after a delay; old dispatch jobs cannot send out of band.
    fixed = [p for p in store.publications() if p["status"] in {"published", "simulated", "sending", "unknown", "scheduled", "manual_ready", "manual_confirmed"} and (p.get("published_at") or p.get("simulated_at") or p.get("scheduled_at")) and (p["episode_id"] != episode_id or p["status"] in TERMINAL)]
    times_by_account = {}
    counts = Counter()
    subjects = {}
    for row in fixed:
        key = (row["platform"], row["account_id"])
        at = instant(row.get("published_at") or row.get("simulated_at") or row["scheduled_at"])
        times_by_account.setdefault(key, []).append(at)
        counts[key+(str(at.astimezone(PARIS).date()),)] += 1
        subjects[key+(str(at.astimezone(PARIS).date()), row.get("segment_id", row["asset_id"]))] = True
    scheduled = archived = blocked = 0
    rows.sort(key=lambda p: (-float(p.get("editorial_score", 0)), p["id"]))
    for row in rows:
        if row["status"] in TERMINAL:
            continue
        try:
            assert_editorial_current(store, row)
        except ValueError as error:
            row.update(status="blocked", blocked_reason=str(error), scheduled_at=None)
            store.save_publication(row, now=now)
            blocked += 1
            continue
        if row.get("qa_status") != "passed":
            row.update(status="blocked", blocked_reason="quality_review_required", scheduled_at=None)
            store.save_publication(row, now=now)
            blocked += 1
            continue
        try:
            from .packaging import assert_reviewed
            assert_reviewed(row, store.get("asset", row["asset_id"]))
        except (ValueError, OSError):
            row.update(status="blocked", blocked_reason="thumbnail_packaging_review_required", scheduled_at=None)
            store.save_publication(row, now=now)
            blocked += 1
            continue
        if row["platform"] != "linkedin" and row["account_id"] not in config["authorized_accounts"][row["platform"]]:
            row.update(status="blocked", blocked_reason="account_not_authorized", scheduled_at=None)
            store.save_publication(row, now=now)
            blocked += 1
            continue
        key = (row["platform"], row["account_id"])
        chosen = None
        spacing = timedelta(minutes=config["schedule"]["minimum_spacing_minutes"])
        for at in local_slots(max(start, now), latest, config["schedule"]["slots_local"]):
            daily_key = key+(str(at.astimezone(PARIS).date()),)
            if counts[daily_key] >= config["schedule"]["maximum_per_day_per_account"]:
                continue
            if any(abs(at-other) < spacing for other in times_by_account.get(key, [])):
                continue
            # Avoid consecutive near-identical subjects on the same account and day.
            topic_key = daily_key+(row.get("segment_id", row["asset_id"]),)
            if topic_key in subjects:
                continue
            chosen = at
            subjects[topic_key] = True
            counts[daily_key] += 1
            times_by_account.setdefault(key, []).append(at)
            break
        if chosen is None:
            row.update(status="archived", blocked_reason="surplus_or_expired_window", scheduled_at=None)
            archived += 1
        else:
            row.update(status="manual_ready" if row["platform"] == "linkedin" else "scheduled", scheduled_at=iso(chosen), window=bounds, blocked_reason=None)
            if row["platform"] == "linkedin":
                row["valid_until"] = iso(end)
            scheduled += 1
        store.save_publication(row, now=now)
        if row["platform"] == "linkedin" and row.get("manual_pack"):
            from pathlib import Path
            import json
            pack_path = Path(row["manual_pack"]) / "pack.json"
            if pack_path.parent.is_dir():
                pack_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        if chosen and row["platform"] != "linkedin":
            job_id = store.enqueue("dispatch", episode_id, {"publication_id": row["id"]}, key="dispatch:"+row["id"], now=chosen)
            store.db.execute("UPDATE jobs SET status='queued',due_at=?,last_error=NULL WHERE id=? AND status IN ('queued','blocked')", (iso(chosen), job_id))
    store.put("window", episode_id, bounds, episode_id=episode_id, now=now)
    store.event("calendar_planned", episode_id, {**bounds, "scheduled": scheduled, "archived": archived, "blocked": blocked}, now=now)
    return {"episode_id": episode_id, **bounds, "scheduled": scheduled, "archived": archived, "blocked": blocked}


def close_cycles(store, config: dict, *, now=None) -> list[str]:
    now = instant(now or utcnow())
    closed = []
    for episode in store.records("episode"):
        if not episode.get("next_filming_at"):
            continue
        end = instant(episode["next_filming_at"])-timedelta(minutes=config["schedule"]["processing_margin_minutes"])
        if now < end:
            continue
        for row in store.publications(episode["episode_id"]):
            if row["status"] not in TERMINAL:
                row.update(status="expired", blocked_reason="cycle_closed")
                store.save_publication(row, now=now)
            elif row["status"] in {"sending", "unknown"}:
                store.event("reconciliation_required", row["id"], {"reason": "cycle_closed_with_uncertain_remote_state"}, now=now)
        store.db.execute("UPDATE jobs SET status='expired' WHERE episode_id=? AND kind='dispatch' AND status IN ('queued','blocked','failed')", (episode["episode_id"],))
        if not store.get("closed_cycle", episode["episode_id"]):
            store.put("closed_cycle", episode["episode_id"], {"closed_at": iso(now)}, episode_id=episode["episode_id"], now=now)
            store.event("cycle_closed", episode["episode_id"], {"metrics_and_experiments_continue": True}, now=now)
            closed.append(episode["episode_id"])
    return closed


def assert_sendable(store, config, publication, *, now=None):
    now = instant(now or utcnow())
    if store.setting("paused", False):
        raise ValueError("queue_paused")
    if publication["status"] not in {"scheduled", "sending"}:
        raise ValueError("publication_not_sendable")
    assert_editorial_current(store, publication)
    episode = store.get("episode", publication["episode_id"])
    start, end = window(episode, config)
    latest = end-timedelta(minutes=config["schedule"]["connector_latency_minutes"])
    if not start <= now < latest:
        raise ValueError("publication_window_expired_or_not_started")
    if not publication.get("scheduled_at") or now < instant(publication["scheduled_at"]):
        raise ValueError("publication_not_due")
    if now-instant(publication["scheduled_at"]) > timedelta(minutes=config["schedule"].get("maximum_lateness_minutes", 15)):
        raise ValueError("missed_slot_replan_required")
    if publication["platform"] == "linkedin":
        raise ValueError("linkedin_manual_only")
    if publication["account_id"] not in config["authorized_accounts"][publication["platform"]]:
        raise ValueError("account_not_authorized")
    daily_sent = 0
    for previous in store.publications(platform=publication["platform"]):
        if previous["id"] == publication["id"] or previous["account_id"] != publication["account_id"]:
            continue
        sent = previous.get("simulated_at") or previous.get("published_at")
        if sent and instant(sent).astimezone(PARIS).date() == now.astimezone(PARIS).date():
            daily_sent += 1
        if sent and timedelta(0) <= now-instant(sent) < timedelta(minutes=config["schedule"]["minimum_spacing_minutes"]):
            raise ValueError("minimum_spacing_replan_required")
        if previous["status"] in {"sending", "unknown"}:
            raise ValueError("account_has_uncertain_dispatch")
    if daily_sent >= config["schedule"]["maximum_per_day_per_account"]:
        raise ValueError("daily_limit_replan_required")
    asset = store.get("asset", publication["asset_id"])
    if not asset or asset.get("qa_status") != "passed" or asset["sha256"] != publication.get("asset_sha256"):
        raise ValueError("asset_or_review_changed")
    from .media import fingerprint
    if fingerprint(__import__("pathlib").Path(asset["path"])) != asset["sha256"]:
        raise ValueError("asset_file_changed")
    from .packaging import assert_reviewed
    assert_reviewed(publication, asset)
