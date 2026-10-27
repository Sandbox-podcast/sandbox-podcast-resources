"""Pure validation and edit decisions for independent horizontal videos."""
from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path

from .storage import digest

VERSION = 1
DIMENSIONS = ("audience", "discussion", "standalone", "hook", "substance", "retention")
WEIGHTS = (15, 20, 25, 15, 15, 10)


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()))


def number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def validate_transcript(value: object, duration: float) -> list[dict]:
    if isinstance(value, dict):
        value = value.get("segments")
    if not isinstance(value, list) or not value:
        raise ValueError("La transcription doit contenir des segments horodatés.")
    result = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("Segment de transcription invalide.")
        start, end, text = row.get("start"), row.get("end"), row.get("text")
        if not number(start) or not number(end) or not 0 <= start < end <= duration + .1:
            raise ValueError("Horodatage de transcription hors de la source.")
        if result and start < result[-1]["end"] - .05:
            raise ValueError("Transcription désordonnée ou segments superposés.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Parole vide dans la transcription.")
        result.append({"start": float(start), "end": min(float(end), duration), "text": text.strip()})
    return result


def read_transcript(path: Path, duration: float, video_id: str | None = None, source_hash: str | None = None) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".jsonl":
        raw = [json.loads(line) for line in text.splitlines() if line.strip()]
    elif path.suffix == ".txt":
        from .editorial import parse_youtube_transcript
        raw = parse_youtube_transcript(text, video_id or "", duration)
    else:
        raw = json.loads(text)
    if isinstance(raw, dict):
        if video_id and raw.get("source_video_id") not in (None, video_id):
            raise ValueError("La transcription appartient à un autre épisode.")
        if source_hash and raw.get("source_sha256") not in (None, source_hash):
            raise ValueError("La transcription appartient à un autre master.")
    return validate_transcript(raw, duration)


def sentences(segments: list[dict]) -> list[dict]:
    """Group ASR fragments at punctuation or pauses; boundaries remain estimates."""
    result, pending = [], []
    for row in segments:
        if pending and (row["start"] - pending[-1]["end"] > 2 or (
            pending[-1]["end"] - pending[0]["start"] >= 5 and row["start"] - pending[-1]["end"] >= .35
        )):
            result.append({"start": pending[0]["start"], "end": pending[-1]["end"], "text": " ".join(s["text"] for s in pending)})
            pending = []
        pending.append(row)
        if re.search(r"[.!?…][\"»']?$", row["text"]):
            result.append({"start": pending[0]["start"], "end": row["end"], "text": " ".join(s["text"] for s in pending)})
            pending = []
    if pending:
        result.append({"start": pending[0]["start"], "end": pending[-1]["end"], "text": " ".join(s["text"] for s in pending)})
    return result


def score(values: dict) -> float:
    if not isinstance(values, dict) or set(values) != set(DIMENSIONS):
        raise ValueError("Les six dimensions éditoriales sont requises.")
    if any(not number(v) or not 0 <= v <= 100 for v in values.values()):
        raise ValueError("Chaque score doit être fini et compris entre 0 et 100.")
    return round(sum(values[k] * w / 100 for k, w in zip(DIMENSIONS, WEIGHTS)), 1)


def _text(value: object, limit: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit or "\x00" in value:
        raise ValueError("Texte éditorial absent ou trop long.")
    return value.strip()


def validate_analysis(raw: object, units: list[dict], count: int = 5, minimum: float = 72) -> dict:
    if not 1 <= count <= 5 or not number(minimum) or not 0 <= minimum <= 100:
        raise ValueError("Au plus cinq vidéos, avec un seuil entre 0 et 100.")
    if not isinstance(raw, dict) or not isinstance(raw.get("candidates"), list) or len(raw["candidates"]) > 30:
        raise ValueError("L'analyse doit contenir au maximum trente candidats.")
    candidates = []
    for item in raw["candidates"]:
        if not isinstance(item, dict):
            raise ValueError("Candidat invalide.")
        title = _text(item.get("title"), 100)
        topic = _text(item.get("topic"), 120)
        thumbnail = _text(item.get("thumbnail_text"), 70)
        if not 3 <= len(thumbnail.split()) <= 5:
            raise ValueError("La miniature doit contenir de trois à cinq mots.")
        ranges = item.get("ranges")
        if not isinstance(ranges, list) or not 1 <= len(ranges) <= 20:
            raise ValueError("Chaque vidéo doit conserver une à vingt plages de phrases.")
        previous = -1
        kept = []
        for pair in ranges:
            if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int for v in pair):
                raise ValueError("Les plages utilisent des indices entiers inclusifs.")
            start, end = pair
            if not 0 <= start <= end < len(units) or start <= previous:
                raise ValueError("Plages invalides, superposées ou hors ordre chronologique.")
            previous = end
            kept.extend(range(start, end + 1))
        hook = item.get("hook")
        if not isinstance(hook, list) or len(hook) != 2 or any(type(v) is not int for v in hook):
            raise ValueError("L'accroche doit citer des phrases de l'émission.")
        hs, he = hook
        if not 0 <= hs <= he < len(units) or any(i not in kept for i in range(hs, he + 1)) or not 5 <= units[he]["end"] - units[hs]["start"] <= 15:
            raise ValueError("L'accroche doit durer 5 à 15 secondes dans le sujet conservé.")
        evidence = item.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {"question", "development", "conclusion"}:
            raise ValueError("Question, développement et conclusion doivent être justifiés.")
        for role, reference in evidence.items():
            if not isinstance(reference, dict) or type(reference.get("index")) is not int or reference["index"] not in kept:
                raise ValueError("Preuve éditoriale hors des paroles conservées.")
            quote = _text(reference.get("quote"), 1500)
            if normalized(quote) not in normalized(units[reference["index"]]["text"]):
                raise ValueError("Une preuve contient des paroles inventées.")
        if not evidence["question"]["index"] < evidence["development"]["index"] < evidence["conclusion"]["index"]:
            raise ValueError("L'ordre question, développement, conclusion doit être conservé.")
        if evidence["question"]["index"] != kept[0] or evidence["conclusion"]["index"] != kept[-1]:
            raise ValueError("Le corps doit commencer par le contexte et finir sur la conclusion justifiée.")
        duration = sum(units[b]["end"] - units[a]["start"] for a, b in ranges) + units[he]["end"] - units[hs]["start"]
        if not 300 <= duration <= 900:
            raise ValueError("La vidéo, accroche comprise, doit durer 5 à 15 minutes.")
        values = item.get("scores")
        editorial_score = score(values)
        candidates.append({"id": digest({"ranges": ranges, "topic": normalized(topic)})[:12], "topic": topic, "title": title,
                           "description": _text(item.get("description"), 3500), "thumbnail_text": thumbnail,
                           "rationale": _text(item.get("rationale"), 2000), "scores": values, "score": editorial_score,
                           "ranges": ranges, "hook": hook, "evidence": evidence, "duration_before_silence_trim": round(duration, 3)})
    selected, rejected = [], []
    for candidate in sorted(candidates, key=lambda c: (-c["score"], c["ranges"][0][0])):
        reason = None
        if candidate["score"] < minimum or candidate["scores"]["standalone"] < 70:
            reason = "Qualité éditoriale insuffisante."
        elif len(selected) >= count:
            reason = "Limite de vidéos atteinte."
        elif any(normalized(candidate["topic"]) == normalized(other["topic"]) or any(
            a <= d and c <= b for a, b in candidate["ranges"] for c, d in other["ranges"]
        ) for other in selected):
            reason = "Sujet similaire ou plages déjà utilisées."
        if reason:
            rejected.append({**candidate, "rejection_reason": reason})
        else:
            selected.append(candidate)
    return {"version": VERSION, "selected": selected, "rejected": rejected,
            "score_notice": "Classement éditorial, sans prédiction de viralité."}


def edit_timeline(candidate: dict, units: list[dict], segments: list[dict]) -> list[dict]:
    """Preview hook then chronological body. Only shorten gaps with no transcribed speech."""
    hs, he = candidate["hook"]
    ranges = [(units[hs]["start"], units[he]["end"], "hook")]
    ranges += [(units[a]["start"], units[b]["end"], "body") for a, b in candidate["ranges"]]
    timeline, cursor = [], 0.0
    for start, end, role in ranges:
        # Keep 180 ms on both sides of any removed pause; never cut inside an ASR segment.
        gaps = [(left["end"] + .18, right["start"] - .18) for left, right in zip(segments, segments[1:])
                if start <= left["end"] < right["start"] <= end and right["start"] - left["end"] > 1.8]
        position = start
        for gap_start, gap_end in gaps + [(end, end)]:
            if gap_start > position:
                length = gap_start - position
                timeline.append({"source_start": round(position, 3), "source_end": round(gap_start, 3),
                                 "output_start": round(cursor, 3), "output_end": round(cursor + length, 3), "role": role})
                cursor += length
            position = gap_end
    # Do not pad a weak/short selection to satisfy the duration requirement.
    if not 300 <= cursor <= 900:
        raise ValueError("La durée après retrait des pauses sort de la plage 5 à 15 minutes.")
    return timeline


def subtitles(timeline: list[dict], segments: list[dict]) -> str:
    from .shorts_core import make_srt
    mapped = []
    for edit in timeline:
        for row in segments:
            start, end = max(row["start"], edit["source_start"]), min(row["end"], edit["source_end"])
            if end > start:
                offset = edit["output_start"] - edit["source_start"]
                mapped.append({"start": round(start + offset, 3), "end": round(end + offset, 3), "text": row["text"]})
    return make_srt(mapped, 0, timeline[-1]["output_end"])
