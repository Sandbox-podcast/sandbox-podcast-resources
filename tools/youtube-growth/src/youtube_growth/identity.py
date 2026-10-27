"""Identity checks shared by every authenticated entry point."""
from __future__ import annotations

import os
import re


# Public channel link observed on the episode page on 2026-10-14.
SANDBOX_CHANNEL_ID = "UCuATIBXo5uvNLVm-gCgMenA"
FIRST_VIDEO_ID = "GgSiPkADCz4"


def expected_channel_id() -> str:
    value = os.environ.get("YOUTUBE_EXPECTED_CHANNEL_ID", SANDBOX_CHANNEL_ID).strip()
    if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", value):
        raise ValueError("YOUTUBE_EXPECTED_CHANNEL_ID doit être un identifiant de chaîne UC valide.")
    return value


def validate_video_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        raise ValueError("L'identifiant vidéo YouTube doit contenir 11 caractères.")
    return value


def verify_channel(service, expected: str | None = None) -> dict:
    target = expected_channel_id()
    if expected is not None and expected != target:
        raise RuntimeError("La chaîne demandée diffère de la chaîne configurée.")
    response = service.channels().list(
        part="id,snippet,contentDetails,statistics,brandingSettings,status", mine=True, maxResults=50,
    ).execute(num_retries=3)
    channels = response.get("items") if isinstance(response, dict) else None
    if not isinstance(channels, list) or len(channels) != 1:
        raise RuntimeError("OAuth doit identifier exactement une chaîne. Aucune écriture autorisée.")
    channel = channels[0]
    if not isinstance(channel, dict) or channel.get("id") != target:
        raise RuntimeError(f"La chaîne OAuth ne correspond pas à {target}. Aucune écriture autorisée.")
    return channel


def verify_video(service, video_id: str, expected: str | None = None) -> dict:
    channel = verify_channel(service, expected)
    response = service.videos().list(
        part="snippet,status,contentDetails,statistics", id=validate_video_id(video_id),
    ).execute(num_retries=3)
    videos = response.get("items") if isinstance(response, dict) else None
    if not isinstance(videos, list) or len(videos) != 1:
        raise RuntimeError("La vidéo source est absente ou inaccessible.")
    video = videos[0]
    if not isinstance(video, dict) or video.get("snippet", {}).get("channelId") != channel["id"]:
        raise RuntimeError("La vidéo n'appartient pas à la chaîne SANDBOX authentifiée.")
    return video
