from __future__ import annotations

import re
import textwrap
from datetime import datetime, timedelta, timezone, tzinfo
from calendar import monthrange
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _last_sunday(year: int, month: int) -> int:
    last_day = monthrange(year, month)[1]
    last_weekday = datetime(year, month, last_day).weekday()
    return last_day - ((last_weekday + 1) % 7)


class _ParisFallback(tzinfo):
    """Fallback rules for EU civil time if a Windows Python install lacks its tzdata package."""

    def _is_dst_local(self, value: datetime) -> bool:
        march = _last_sunday(value.year, 3)
        october = _last_sunday(value.year, 10)
        start = datetime(value.year, 3, march, 3)
        end = datetime(value.year, 10, october, 2)
        wall = value.replace(tzinfo=None)
        if wall.date() == end.date() and wall.hour == 2:
            return value.fold == 0
        if wall.date() == start.date() and wall.hour == 2:
            return value.fold == 1
        return start <= wall < end

    def utcoffset(self, value: datetime | None) -> timedelta:
        if value is None:
            return timedelta(hours=1)
        return timedelta(hours=2 if self._is_dst_local(value) else 1)

    def dst(self, value: datetime | None) -> timedelta:
        if value is None:
            return timedelta(0)
        return timedelta(hours=1 if self._is_dst_local(value) else 0)

    def tzname(self, value: datetime | None) -> str:
        return "CEST" if value is not None and self._is_dst_local(value) else "CET"

    def fromutc(self, value: datetime) -> datetime:
        if value.tzinfo is not self:
            raise ValueError("fromutc attend une date UTC associée à ce fuseau.")
        utc_wall = value.replace(tzinfo=None)
        start = datetime(value.year, 3, _last_sunday(value.year, 3), 1)
        end = datetime(value.year, 10, _last_sunday(value.year, 10), 1)
        summer = start <= utc_wall < end
        local = utc_wall + timedelta(hours=2 if summer else 1)
        ambiguous_hour = local.month == 10 and local.day == _last_sunday(local.year, 10) and local.hour == 2
        return local.replace(tzinfo=self, fold=0 if summer or not ambiguous_hour else 1)


try:
    PARIS: tzinfo = ZoneInfo("Europe/Paris")
except ZoneInfoNotFoundError:
    PARIS = _ParisFallback()


def _words(value: str) -> list[str]:
    return re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE)


def _contains_phrase(text: str, phrase: str) -> bool:
    source_words = _words(text)
    phrase_words = _words(phrase)
    if not phrase_words:
        return False
    return any(source_words[index : index + len(phrase_words)] == phrase_words for index in range(len(source_words)))


def validate_clip_candidates(
    raw: Any,
    segments: list[dict[str, Any]],
    requested_count: int,
    min_seconds: float = 15,
    max_seconds: float = 60,
) -> list[dict[str, Any]]:
    """Valide les sélections du modèle contre les horodatages et les paroles transcrites."""
    if not isinstance(raw, dict) or not isinstance(raw.get("clips"), list):
        raise ValueError("Le modèle n'a pas renvoyé une liste de clips valide.")
    if not segments:
        raise ValueError("La transcription ne contient aucun segment exploitable.")

    clips: list[dict[str, Any]] = []
    used_indexes: set[int] = set()
    for item in raw["clips"][:requested_count]:
        if not isinstance(item, dict):
            continue
        start_index = item.get("start_index")
        end_index = item.get("end_index")
        title = item.get("title")
        if (
            not isinstance(start_index, int)
            or isinstance(start_index, bool)
            or not isinstance(end_index, int)
            or isinstance(end_index, bool)
            or not isinstance(title, str)
        ):
            continue
        if start_index < 0 or end_index < start_index or end_index >= len(segments):
            continue
        if any(index in used_indexes for index in range(start_index, end_index + 1)):
            continue
        start = float(segments[start_index]["start"])
        end = float(segments[end_index]["end"])
        duration = end - start
        if not min_seconds <= duration <= max_seconds:
            continue
        transcript = " ".join(str(segment.get("text", "")) for segment in segments[start_index : end_index + 1])
        clean_title = " ".join(title.split()).strip(" \t\r\n\"'«»“”")
        if not clean_title or len(_words(clean_title)) > 9 or not _contains_phrase(transcript, clean_title):
            continue
        clips.append(
            {
                "start_index": start_index,
                "end_index": end_index,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
                "title": clean_title,
            }
        )
        used_indexes.update(range(start_index, end_index + 1))

    if not clips:
        raise ValueError("Aucun clip proposé ne respecte la durée et la validation des paroles.")
    return sorted(clips, key=lambda clip: clip["start"])


def next_publish_time(now: datetime | None = None) -> datetime:
    """Choisit demain à 17 h, heure de Paris, pour laisser du temps à la relecture."""
    current = now or datetime.now(PARIS)
    if current.tzinfo is None:
        raise ValueError("L'heure de référence doit inclure un fuseau horaire.")
    tomorrow = current.astimezone(PARIS).date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 17, 0, tzinfo=PARIS)


def parse_publish_time(value: str | None, now: datetime | None = None) -> datetime:
    if not value:
        return next_publish_time(now)
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("La date doit être au format ISO 8601 et inclure son fuseau, par exemple 2026-10-14T17:00:00+02:00.") from error
    if result.tzinfo is None:
        raise ValueError("La date doit inclure son fuseau horaire, par exemple +02:00 ou Z.")
    if result <= (now or datetime.now(timezone.utc)):
        raise ValueError("La première publication doit être dans le futur.")
    return result


def daily_publish_times(first: datetime, count: int) -> list[str]:
    if first.tzinfo is None:
        raise ValueError("L'heure de publication doit inclure son fuseau horaire.")
    paris_first = first.astimezone(PARIS)
    results = []
    for day in range(count):
        local = paris_first + timedelta(days=day)
        results.append(local.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    return results


def format_publish_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("L'heure de publication doit inclure son fuseau horaire.")
    return parsed.astimezone(PARIS).strftime("%Y-%m-%d %H:%M %Z (Paris)")


def srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"


def make_srt(segments: list[dict[str, Any]], start: float, end: float) -> str:
    entries: list[str] = []
    for segment in segments:
        segment_start = max(start, float(segment["start"]))
        segment_end = min(end, float(segment["end"]))
        text = " ".join(str(segment.get("text", "")).split())
        if not text or segment_end <= segment_start:
            continue
        wrapped = textwrap.fill(text, width=38, break_long_words=False, break_on_hyphens=False)
        entries.append(
            f"{len(entries) + 1}\n{srt_timestamp(segment_start - start)} --> {srt_timestamp(segment_end - start)}\n{wrapped}"
        )
    if not entries:
        raise ValueError("Aucun sous-titre n'est disponible pour ce clip.")
    return "\n\n".join(entries) + "\n"
