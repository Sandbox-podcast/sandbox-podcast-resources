"""Import the existing read-only YouTube audit without flattening native dimensions."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .contracts import digest, instant, iso
from .analytics import validate_observation

METRICS = {"views": "count", "engagedViews": "count", "estimatedMinutesWatched": "minutes",
           "averageViewDuration": "seconds", "averageViewPercentage": "percent", "subscribersGained": "count",
           "subscribersLost": "count", "likes": "count", "comments": "count", "shares": "count",
           "audienceWatchRatio": "ratio", "relativeRetentionPerformance": "ratio"}
DIMENSIONS = {"day", "insightTrafficSourceType", "elapsedVideoTimeRatio"}
PACIFIC = ZoneInfo("America/Los_Angeles")


def midnight(day):
    return datetime.combine(day, time(), PACIFIC)


def import_audit(store, config, audit, *, fixture=False, now=None):
    if audit.get("identity_verified") is not True:
        raise ValueError("Audit avec contrôle d'identité requis.")
    channel = audit.get("channel", {}).get("id")
    video = audit.get("video", {}).get("id")
    if not isinstance(video, str) or channel not in config["authorized_accounts"]["youtube"]:
        raise ValueError("Chaîne Analytics non autorisée ou vidéo absente.")
    captured = instant(audit["captured_at"])
    if now is not None and captured > instant(now):
        raise ValueError("Collecte Analytics future.")
    start, end = (date.fromisoformat(audit["period"][k]) for k in ("start", "end"))
    if start > end:
        raise ValueError("Période Analytics inversée.")
    rows, availability = [], {}
    for name in ("channel_daily", "video_daily", "traffic", "retention"):
        report = audit.get("analytics", {}).get(name, {})
        availability[name] = report.get("status", "not_supplied")
        if report.get("status") != "available":
            continue
        data = report.get("data", {})
        columns = data.get("columns", [])
        if not isinstance(columns, list) or len(columns) != len(set(columns)) or set(columns)-DIMENSIONS-set(METRICS):
            raise ValueError("Colonnes Analytics non reconnues ; ne pas inventer leur définition.")
        for raw in data.get("rows", []):
            if not isinstance(raw, list) or len(raw) != len(columns):
                raise ValueError("Ligne Analytics non conforme.")
            line = dict(zip(columns, raw))
            first, last = (date.fromisoformat(line["day"]), date.fromisoformat(line["day"])) if "day" in line else (start, end)
            if not start <= first <= last <= end:
                raise ValueError("Jour Analytics hors de la période demandée.")
            dimensions = {k: line[k] for k in DIMENSIONS if k in line and k != "day"}
            scope, entity = ("account", channel) if name == "channel_daily" else ("media", video)
            for metric in set(line) & set(METRICS):
                if line[metric] is None:
                    continue
                value = {"platform": "youtube", "account_id": channel, "scope": scope, "entity_id": entity,
                    "metric": metric, "value": line[metric], "unit": METRICS[metric], "denominator": None,
                    "statistic": "interval", "source": "youtube_analytics_v2:"+name,
                    "definition": "https://developers.google.com/youtube/analytics/metrics#"+metric,
                    "definition_version": "youtube-analytics-v2-import-v1", "data_class": "synthetic_fixture" if fixture or audit.get("synthetic") else "observed",
                    "period_start": iso(midnight(first)), "period_end": iso(midnight(last+timedelta(days=1))),
                    "collected_at": iso(captured), "aggregation_timezone": "America/Los_Angeles", "dimensions": dimensions,
                    "audit_sha256": digest(audit)}
                value["observation_id"] = "yt-"+digest(value)
                rows.append(validate_observation(value))
    with store.transaction():
        for row in rows:
            store.put("observation", row["observation_id"], row, now=now)
        store.event("analytics_imported", video, {"observations": len(rows), "availability": availability,
                    "synthetic": fixture or audit.get("synthetic", False)}, now=now)
    return {"status": "imported", "observation_count": len(rows), "availability": availability,
            "missing_metrics": ["impressions", "thumbnail_ctr", "new_viewers"],
            "missing_notice": "Importer les relevés Studio disponibles avec leurs définitions ; aucune valeur estimée.",
            "data_class": "synthetic_fixture" if fixture or audit.get("synthetic") else "observed"}
