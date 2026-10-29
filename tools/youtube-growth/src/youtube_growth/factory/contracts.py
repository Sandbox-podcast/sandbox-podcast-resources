"""Validated input contracts shared by CLI, workers and scheduler."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[5]
UTC = timezone.utc
PARIS = ZoneInfo("Europe/Paris")
PLATFORMS = {"youtube", "tiktok", "instagram", "x", "linkedin"}


def utcnow() -> datetime:
    return datetime.now(UTC)


def instant(value: str | datetime) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Une date doit inclure son décalage UTC.")
    return parsed.astimezone(UTC)


def iso(value: str | datetime) -> str:
    return instant(value).isoformat()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Un objet JSON est requis.")
    return value


def load_config(path: Path | None = None) -> dict:
    value = load_json(path or ROOT / "config/factory.json")
    if value.get("version") != 1 or value.get("mode") != "simulation" or value.get("live_enabled") is not False:
        raise ValueError("Cette livraison exige mode=simulation et live_enabled=false.")
    if value.get("timezone") != "Europe/Paris":
        raise ValueError("Le fuseau éditorial est Europe/Paris.")
    accounts = value.get("authorized_accounts")
    if not isinstance(accounts, dict) or set(accounts) != PLATFORMS:
        raise ValueError("Une liste explicite de comptes est requise pour chaque plateforme.")
    for platform, items in accounts.items():
        if not isinstance(items, list) or any(not isinstance(x, str) or not x.strip() for x in items):
            raise ValueError(f"Comptes invalides : {platform}.")
    schedule = value["schedule"]
    for field in ("minimum_spacing_minutes", "maximum_per_day_per_account", "processing_margin_minutes", "connector_latency_minutes", "maximum_lateness_minutes"):
        number = schedule[field]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number <= 0:
            raise ValueError(f"Paramètre de calendrier invalide : {field}.")
    for slot in schedule["slots_local"]:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", slot):
            raise ValueError("Créneau local invalide.")
    if not schedule["slots_local"]:
        raise ValueError("Au moins un créneau local est requis.")
    for field in ("lease_seconds", "maximum_attempts", "retry_seconds"):
        if type(value["runtime"][field]) is not int or value["runtime"][field] < 1:
            raise ValueError(f"Paramètre runtime invalide : {field}.")
    for field, default in (("watch_verify_seconds", 3600), ("idle_max_seconds", 60)):
        number = value["runtime"].get(field, default)
        if type(number) is not int or number < 1:
            raise ValueError(f"Paramètre runtime invalide : {field}.")
    for field in ("interval_hours", "report_interval_hours"):
        if type(value["metrics"][field]) not in (int, float) or not math.isfinite(value["metrics"][field]) or value["metrics"][field] <= 0:
            raise ValueError(f"Fréquence de métriques invalide : {field}.")
    if value["budgets"]["external_calls_enabled"] is not False:
        raise ValueError("Les appels externes payants restent désactivés dans cette livraison.")
    minimum = value.get("editorial", {}).get("minimum_score", 70)
    if type(minimum) not in (int, float) or not math.isfinite(minimum) or not 0 <= minimum <= 100:
        raise ValueError("Seuil éditorial invalide.")
    generation = value.get("generation", {})
    if generation.get("network", False) is not False or generation.get("cost_per_call", 0) != 0:
        raise ValueError("La génération configurée doit rester locale et sans coût.")
    from .local_models import settings
    settings(value)
    return value


def validate_episode(value: dict, *, base: Path | None = None) -> dict:
    """Keep absent downstream fields explicit, without blocking local analysis."""
    value = dict(value)
    if value.get("version") != 1 or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", str(value.get("episode_id", ""))):
        raise ValueError("Manifest version 1 et episode_id stable en minuscules requis.")
    if not isinstance(value.get("title"), str) or not value["title"].strip():
        raise ValueError("Titre requis.")
    if value.get("timezone", "Europe/Paris") != "Europe/Paris":
        raise ValueError("Fuseau Europe/Paris requis.")
    value["timezone"] = "Europe/Paris"
    if type(value.get("local_autonomy", False)) is not bool:
        raise ValueError("local_autonomy doit être un booléen.")
    source = value.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Chemin source requis.")
    for field in ("source", "transcript", "evidence"):
        if value.get(field):
            path = Path(value[field])
            value[field] = str(((base or ROOT) / path).resolve() if not path.is_absolute() else path.resolve())
    for field in ("planned_publication_at", "next_filming_at", "available_at", "availability_checked_at"):
        if value.get(field):
            value[field] = iso(value[field])
    availability = value.get("availability", "unknown")
    if availability not in {"unknown", "pending", "available", "unavailable"}:
        raise ValueError("Disponibilité invalide.")
    value["availability"] = availability
    if availability == "available" and not all(value.get(f) for f in ("available_at", "availability_checked_at", "full_episode_url", "full_episode_id", "availability_evidence")):
        raise ValueError("Une disponibilité confirmée exige URL, identifiant, heure et preuve.")
    if value.get("full_episode_url"):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(value["full_episode_url"])
        if parsed.scheme != "https" or parsed.hostname not in {"www.youtube.com", "youtube.com", "youtu.be"} or parsed.username or parsed.password:
            raise ValueError("Destination de l'émission : URL YouTube HTTPS requise.")
        if parsed.hostname != "youtu.be" and parsed.path != "/watch":
            raise ValueError("Une URL de lecture /watch de l'émission est requise.")
        remote_id = parsed.path.strip("/") if parsed.hostname == "youtu.be" else parse_qs(parsed.query).get("v", [None])[0]
        if remote_id != value.get("full_episode_id") or not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(remote_id)):
            raise ValueError("L'URL et l'identifiant de l'émission diffèrent.")
    value.setdefault("synthetic", False)
    return value


def episode_blockers(episode: dict) -> list[str]:
    result = []
    for field in ("next_filming_at", "full_episode_url", "full_episode_id"):
        if not episode.get(field):
            result.append(f"missing:{field}")
    if episode.get("availability") != "available":
        result.append("full_episode_not_available")
    if episode.get("source_revision_requires_reconciliation"):
        result.append("source_revision_requires_reconciliation")
    return result
