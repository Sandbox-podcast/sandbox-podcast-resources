from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .identity import verify_channel, verify_video


def load_credentials(token_path: Path | None = None):
    raw = os.environ.get("YOUTUBE_OAUTH_TOKEN_JSON", "").strip()
    if not raw and token_path and token_path.is_file():
        raw = token_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as error:
        raise RuntimeError("Installez tools/youtube-growth/requirements.txt avant l'exécution.") from error

    try:
        info: Any = json.loads(raw)
        if not isinstance(info, dict):
            raise ValueError("Le secret OAuth doit être un objet JSON.")
        credentials = Credentials.from_authorized_user_info(info)
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError("Le jeton OAuth fourni par l'environnement ou le fichier local est invalide.") from error
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


def build_youtube_service(token_path: Path | None = None):
    credentials = load_credentials(token_path)
    if credentials is None:
        return None
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def build_analytics_service(token_path: Path | None = None):
    credentials = load_credentials(token_path)
    if credentials is None:
        return None
    from googleapiclient.discovery import build
    return build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)


def channel_context(service) -> tuple[str, str]:
    channel = verify_channel(service)
    return channel["id"], channel["contentDetails"]["relatedPlaylists"]["uploads"]


def upload_video_ids(service, uploads_playlist_id: str, limit: int = 50) -> list[str]:
    result: list[str] = []
    next_page_token = None
    while len(result) < limit:
        page = service.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, limit - len(result)),
            pageToken=next_page_token,
        ).execute()
        for item in page.get("items", []):
            video_id = item.get("contentDetails", {}).get("videoId")
            if video_id:
                result.append(video_id)
        next_page_token = page.get("nextPageToken")
        if not next_page_token:
            break
    return result


def videos_by_id(service, video_ids: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(video_ids), 50):
        response = service.videos().list(part="snippet,status,contentDetails", id=",".join(video_ids[start : start + 50]), maxResults=50).execute()
        for video in response.get("items", []):
            result[video["id"]] = video
    return result


def list_recent_comment_threads(service, channel_id: str, max_pages: int = 10) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    next_page_token = None
    for _ in range(max_pages):
        page = service.commentThreads().list(
            part="snippet,replies",
            allThreadsRelatedToChannelId=channel_id,
            maxResults=100,
            order="time",
            pageToken=next_page_token,
        ).execute()
        result.extend(page.get("items", []))
        next_page_token = page.get("nextPageToken")
        if not next_page_token:
            break
    return result


def post_top_level_comment(service, channel_id: str, video_id: str, text: str) -> str:
    verify_video(service, video_id, channel_id)
    response = service.commentThreads().insert(
        part="snippet",
        body={"snippet": {"channelId": channel_id, "videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}},
    ).execute()
    return response["id"]


def post_reply(service, parent_id: str, text: str) -> str:
    channel = verify_channel(service)
    parent = service.comments().list(part="snippet", id=parent_id).execute(num_retries=3)
    items = parent.get("items", [])
    if len(items) != 1 or items[0].get("snippet", {}).get("channelId") != channel["id"]:
        raise RuntimeError("Le commentaire parent n'appartient pas à SANDBOX.")
    response = service.comments().insert(
        part="snippet",
        body={"snippet": {"parentId": parent_id, "textOriginal": text}},
    ).execute()
    return response["id"]


def top_level_comment_exists(service, video_id: str, channel_id: str, text: str) -> bool:
    page = service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, order="time").execute()
    for thread in page.get("items", []):
        top = thread.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        author_id = top.get("authorChannelId", {}).get("value")
        original = top.get("textOriginal", top.get("textDisplay", ""))
        if author_id == channel_id and original.strip() == text.strip():
            return True
    return False
