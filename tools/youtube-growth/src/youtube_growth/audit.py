from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

from .identity import FIRST_VIDEO_ID, verify_channel, verify_video
from .storage import now_iso, save_json


STUDIO_TASKS = {
    "podcast": "Dans Studio, Contenu, Playlists, définir la playlist des émissions comme podcast et vérifier son éligibilité.",
    "test_compare": "Dans les détails de la vidéo, ouvrir Test & Compare, charger jusqu'à trois variantes, puis consigner le résultat natif et sa part de temps de visionnage.",
    "related_video": "Dans les détails de chaque Short, choisir l'émission comme vidéo associée (fonctionnalités avancées requises).",
    "pin_comment": "Dans les commentaires de la vidéo, épingler le commentaire de discussion validé.",
    "community": "Vérifier l'accès aux posts dans Studio et publier les textes relus depuis l'onglet Posts.",
    "end_screens": "Dans l'éditeur de la vidéo, ajouter l'écran de fin et les fiches vers les contenus existants.",
}


def _items(resource, **kwargs) -> list[dict]:
    results = []
    token = None
    for _ in range(100):
        page = resource.list(**kwargs, maxResults=50, pageToken=token).execute(num_retries=3)
        if not isinstance(page, dict) or not isinstance(page.get("items", []), list):
            raise ValueError("Réponse YouTube non conforme.")
        if any(not isinstance(item, dict) for item in page.get("items", [])):
            raise ValueError("Élément YouTube non conforme.")
        results.extend(page.get("items", []))
        token = page.get("nextPageToken")
        if not token:
            return results
    raise RuntimeError("Pagination trop longue. Réduisez le périmètre de collecte.")


def _optional_read(call) -> dict:
    try:
        return {"status": "available", "data": call()}
    except Exception as error:
        # Only API errors are optional. Programming and filesystem errors must propagate.
        status = getattr(getattr(error, "resp", None), "status", None)
        if not isinstance(status, int):
            raise
        return {"status": "unavailable", "http_status": status, "data": None}


def _single_items(resource, **kwargs) -> list[dict]:
    # channelSections.list and captions.list do not expose pagination parameters.
    raw = resource.list(**kwargs).execute(num_retries=3)
    if not isinstance(raw, dict) or not isinstance(raw.get("items", []), list) or any(not isinstance(item, dict) for item in raw.get("items", [])):
        raise ValueError("Réponse YouTube non conforme.")
    return raw.get("items", [])


def analytics_reports(service, channel_id: str, video_id: str, start: date, end: date) -> dict:
    if start > end:
        raise ValueError("La période Analytics est inversée.")
    queries = {
        "channel_daily": {"dimensions": "day", "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments,shares"},
        "video_daily": {"dimensions": "day", "metrics": "views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost", "filters": f"video=={video_id}"},
        "traffic": {"dimensions": "insightTrafficSourceType", "metrics": "views,estimatedMinutesWatched", "filters": f"video=={video_id}"},
        "retention": {"dimensions": "elapsedVideoTimeRatio", "metrics": "audienceWatchRatio,relativeRetentionPerformance", "filters": f"video=={video_id}"},
    }
    results = {}
    for name, query in queries.items():
        def read(query=query):
            raw = service.reports().query(ids=f"channel=={channel_id}", startDate=start.isoformat(), endDate=end.isoformat(), **query).execute(num_retries=3)
            if not isinstance(raw, dict):
                raise ValueError("Rapport Analytics non conforme.")
            headers = raw.get("columnHeaders", [])
            rows = raw.get("rows", [])
            if not isinstance(headers, list) or not isinstance(rows, list):
                raise ValueError("Colonnes ou lignes Analytics non conformes.")
            names = [item["name"] for item in headers if isinstance(item, dict) and isinstance(item.get("name"), str)]
            if len(names) != len(headers) or any(not isinstance(row, list) or len(row) != len(names) for row in rows):
                raise ValueError("Dimensions des lignes Analytics non conformes.")
            if any(isinstance(value, bool) or not isinstance(value, (str, int, float, type(None))) or (isinstance(value, float) and not math.isfinite(value)) for row in rows for value in row):
                raise ValueError("Valeurs Analytics non conformes.")
            return {"columns": names, "rows": rows}
        result = _optional_read(read)
        if result["status"] == "available" and not result["data"]["rows"]:
            result["status"] = "no_data"
        results[name] = {**result, "query": query}
    # These are not channel-report metrics. Studio exports may supply them later.
    results["studio_only"] = {"thumbnail_impressions": None, "thumbnail_ctr": None, "returning_viewers": None, "short_to_episode_attribution": None, "reason": "Non fournis par ces rapports. Export Studio requis; aucune estimation substituée."}
    return results


def collect_audit(youtube, analytics=None, video_id: str = FIRST_VIDEO_ID, start: date | None = None, end: date | None = None) -> dict:
    channel = verify_channel(youtube)
    video = verify_video(youtube, video_id)
    end = end or date.today() - timedelta(days=1)
    start = start or end - timedelta(days=27)
    uploads_id = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not isinstance(uploads_id, str):
        raise ValueError("Playlist des uploads absente de la réponse YouTube.")
    audit = {
        "version": 1, "captured_at": now_iso(), "period": {"start": start.isoformat(), "end": end.isoformat()},
        "identity_verified": True, "channel": channel, "video": video,
        "uploads": _items(youtube.playlistItems(), part="snippet,contentDetails", playlistId=uploads_id),
        "playlists": _items(youtube.playlists(), part="snippet,status,contentDetails", mine=True),
        "sections": _optional_read(lambda: _single_items(youtube.channelSections(), part="snippet,contentDetails", mine=True)),
        "comments": _optional_read(lambda: _items(youtube.commentThreads(), part="snippet,replies", videoId=video_id, order="time", textFormat="plainText")),
        "captions": _optional_read(lambda: _single_items(youtube.captions(), part="snippet", videoId=video_id)),
        "analytics": analytics_reports(analytics, channel["id"], video_id, start, end) if analytics else {"status": "not_connected", "reason": "OAuth Analytics absent."},
        "studio_tasks": STUDIO_TASKS,
    }
    return audit


def audit_markdown(audit: dict) -> str:
    video = audit["video"]
    channel = audit["channel"]
    lines = ["# Audit YouTube SANDBOX", "", f"Relevé : {audit['captured_at']}", f"Chaîne OAuth vérifiée : {channel['id']}", f"Vidéo : https://www.youtube.com/watch?v={video['id']}", "", "Les statistiques suivantes sont les compteurs de la Data API, à la date du relevé.", "", "```json", json.dumps({"channel": channel.get("statistics", {}), "video": video.get("statistics", {})}, ensure_ascii=False, indent=2), "```", "", f"Playlists : {len(audit['playlists'])}.", "", "Analytics :"]
    for name, result in audit["analytics"].items():
        if isinstance(result, dict) and "status" in result:
            lines.append(f"- {name} : {result['status']}.")
    lines.extend(["", "Les détails bruts restent dans audit.json. Une absence de données ne vaut pas zéro.", "", "Finalisations Studio :", ""])
    lines.extend(f"- {name} : {task}" for name, task in STUDIO_TASKS.items())
    return "\n".join(lines) + "\n"


def save_audit(audit: dict, directory: Path) -> None:
    # Personal comments and Analytics stay in ignored, access-controlled storage.
    save_json(directory / "audit.json", audit)
    (directory / "audit.md").write_text(audit_markdown(audit), encoding="utf-8")
