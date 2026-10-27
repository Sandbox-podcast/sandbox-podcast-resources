"""Evidence-based preparation for native YouTube tools. No media download."""
from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .identity import validate_video_id
from .shorts_core import PARIS
from .storage import digest, save_json


def parse_youtube_transcript(text: str, video_id: str, duration: float) -> list[dict]:
    validate_video_id(video_id)
    if f"Video ID: {video_id}" not in text:
        raise ValueError("La transcription exportée ne correspond pas à la vidéo demandée.")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("La durée de la vidéo doit être positive et finie.")
    rows = []
    for match in re.finditer(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+)$", text, re.M):
        parts = [int(part) for part in match[1].split(":")]
        if any(part >= 60 for part in parts[1:]):
            raise ValueError("Horodatage de transcription invalide.")
        start = 0
        for part in parts:
            start = start * 60 + part
        if start >= duration or (rows and start < rows[-1]["start"]):
            raise ValueError("Horodatages de transcription hors limites ou désordonnés.")
        if rows and start == rows[-1]["start"]:
            rows[-1]["text"] += " " + match[2].strip()
        else:
            rows.append({"start": float(start), "text": match[2].strip()})
    if not rows:
        raise ValueError("Aucun sous-titre horodaté dans l'export YouTube.")
    for index, row in enumerate(rows):
        row["end"] = rows[index + 1]["start"] if index + 1 < len(rows) else duration
        row["end_inferred"] = True
    return rows


def weekly_slots(first: datetime, count: int, per_week: int = 3) -> list[str]:
    if first.tzinfo is None or per_week not in {2, 3, 4} or not 0 <= count <= 30:
        raise ValueError("Calendrier invalide : fuseau requis, 2 à 4 publications par semaine, 30 éléments au maximum.")
    first = first.astimezone(PARIS)
    return [(first + timedelta(days=(index // per_week) * 7 + (index % per_week) * 7 // per_week)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z") for index in range(count)]


def prepare_native_pack(segments: list[dict], spec: object, video_id: str, duration: float, first: datetime) -> dict:
    validate_video_id(video_id)
    if not isinstance(spec, dict) or spec.get("video_id") != video_id or not isinstance(spec.get("candidates"), list):
        raise ValueError("Le dossier éditorial doit contenir video_id et candidates.")
    if not 1 <= len(spec["candidates"]) <= 10:
        raise ValueError("Préparez au maximum dix candidats.")
    source_title = spec.get("source_title", "l'émission SANDBOX")
    episode_url = spec.get("episode_url", "https://www.sandboxpodcast.fr/episodes")
    if not isinstance(source_title, str) or not isinstance(episode_url, str) or not re.fullmatch(r"https://www\.sandboxpodcast\.fr/episodes(?:/\d+)?", episode_url):
        raise ValueError("Titre source et URL de la fiche d'épisode invalides.")
    rows = []
    identities = set()
    selected_intervals = []
    for item in spec["candidates"]:
        if not isinstance(item, dict):
            raise ValueError("Candidat non conforme.")
        start, end = item.get("start"), item.get("end")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, end)):
            raise ValueError("Début et fin doivent être des nombres finis.")
        if not 0 <= start < end <= duration or not 5 <= end - start <= 60:
            raise ValueError("Le parcours natif retenu accepte des extraits de 5 à 60 secondes.")
        title, reason = item.get("title"), item.get("reason")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100 or not isinstance(reason, str) or not reason.strip():
            raise ValueError("Titre (100 caractères maximum) et motif requis.")
        if not isinstance(item.get("selected", False), bool):
            raise ValueError("selected doit être un booléen.")
        if not any(s["start"] < end and s["end"] > start for s in segments):
            raise ValueError("Aucune parole transcrite dans cet extrait.")
        clip_id = digest({"video_id": video_id, "start": start, "end": end})[:16]
        if clip_id in identities:
            raise ValueError("Le même extrait figure deux fois dans le dossier.")
        identities.add(clip_id)
        selected = item.get("selected", False)
        if selected:
            if any(start < previous_end and previous_start < end for previous_start, previous_end in selected_intervals):
                raise ValueError("Les extraits sélectionnés se chevauchent.")
            selected_intervals.append((start, end))
        rows.append({"id": clip_id, "start": start, "end": end, "duration": end-start, "title": title.strip(), "reason": reason.strip(), "selected": selected,
                     "quote_raw": " ".join(s["text"] for s in segments if s["start"] < end and s["end"] > start),
                     "source_url": f"https://www.youtube.com/watch?v={video_id}&t={int(start)}s", "status": "identified", "published_url": None,
                     "description": f"Extrait de {source_title}. La discussion complète : https://www.youtube.com/watch?v={video_id}&t={int(start)}s\nSources : {episode_url}\n#IA #Sandbox", "review_required": ["écoute des limites", "correction des sous-titres", "cadrage", "identité de la chaîne"]})
    selected_rows = [row for row in rows if row["selected"]]
    for row, slot in zip(selected_rows, weekly_slots(first, len(selected_rows)), strict=True):
        row["proposed_publish_at"] = slot
    return {"version": 1, "source_video_id": video_id, "source_duration": duration, "mode": "youtube_native", "transcript_sha256": digest(segments), "transcription_reviewed": False,
            "note": "Calendrier proposé. Aucun Clip ni Short créé par cette commande. Les horodatages viennent de sous-titres automatiques, avec fins inférées.", "candidates": rows}


def save_native_pack(pack: dict, directory: Path) -> None:
    save_json(directory / "native-pack.json", pack)
    lines = ["# Extraits SANDBOX à créer dans YouTube", "", pack["note"], "", "Pour un Short : application YouTube, compte SANDBOX, vidéo source, Remix, Convertir en Short. La limite de ce parcours est de 60 secondes. Vérifier la mise en page, les sous-titres et la vidéo liée avant publication.", "", "Pour un Clip : bouton Clip s'il est disponible, sélectionner le passage (5 à 60 secondes), ajouter un titre et partager. Le lien créé reste un extrait de l'émission; il ne constitue pas une nouvelle vidéo verticale.", ""]
    for row in pack["candidates"]:
        start = f"{int(row['start'])//60:02d}:{int(row['start'])%60:02d}"
        end = f"{int(row['end'])//60:02d}:{int(row['end'])%60:02d}"
        lines.extend([f"## {row['title']}", "", f"{start} à {end}, {row['duration']:g} s. {'Sélectionné' if row['selected'] else 'Réserve'}.", f"[Écouter le passage]({row['source_url']})", "", row["reason"], "", "Transcription automatique brute :", "", "> " + row["quote_raw"].replace("\n", " "), "", "Description proposée :", "", row["description"], "", f"Statut : {row['status']}. Date proposée : {row.get('proposed_publish_at', 'aucune')}", ""])
    (directory / "native-pack.md").write_text("\n".join(lines), encoding="utf-8")
