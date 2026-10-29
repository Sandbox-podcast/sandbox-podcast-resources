"""Configuration, text normalization and timestamp contracts."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[5]
CRITERIA = {"outperformance", "growth", "confirmation", "competition", "production", "french_relevance"}
SOURCES = {"trends", "news", "reddit", "hackernews", "youtube"}
STOP = set("the a an of and to for with in on is new this that des les une un du de la le et en au aux pour sur avec dans est nouveau nouvelle how why what comment pourquoi voici more plus video videos youtube ai ia tech technology technologie intelligence artificial artificielle".split())


def instant(value):
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Date avec fuseau requise.")
    return result.astimezone(timezone.utc)


def stamp(value=None):
    return instant(value or datetime.now(timezone.utc)).isoformat()


def key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()[:24]


def plain(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))


def tokens(value):
    return set(re.findall(r"[a-z0-9]+", plain(value))) - STOP


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def config(path=None, mode=None):
    value = deepcopy(load_json(path or ROOT / "config/youtube-trend-hunter.json"))
    if mode:
        value["mode"] = mode
    if value.get("version") != 1 or value.get("mode") not in {"general", "ai-tech"}:
        raise ValueError("Configuration version 1 ; mode general ou ai-tech requis.")
    if value.get("language") != "fr":
        raise ValueError("La rédaction automatique de cette version prend en charge fr.")
    for name, lo, hi in (("window_days", 1, 7), ("recommendations", 1, 10), ("minimum_score", 0, 100), ("max_video_seconds", 120, 300), ("max_difficulty", 1, 3), ("repeat_after_hours", 0, 168), ("repeat_score_increase", 1, 100)):
        if type(value.get(name)) is not int or not lo <= value[name] <= hi:
            raise ValueError("Paramètre invalide : "+name)
    if not value.get("regions") or any(not re.fullmatch(r"[A-Z]{2}", r) for r in value["regions"]):
        raise ValueError("Codes de région ISO à deux lettres requis.")
    if set(value["sources"]) != SOURCES or any(type(v) is not bool for v in value["sources"].values()):
        raise ValueError("Sources inconnues ou activation non booléenne.")
    weights = value["weights"]
    if set(weights) != CRITERIA or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("Poids finis et positifs ou nuls requis.")
    for group in ("http", "youtube"):
        for name, number in value[group].items():
            if type(number) is not int or number < 0:
                raise ValueError(f"Budget invalide : {group}.{name}")
    if not 1 <= value["http"]["timeout_seconds"] <= 60 or value["http"]["max_requests_per_run"] < 1:
        raise ValueError("Timeout de 1 à 60s et budget HTTP positif requis.")
    yt = value["youtube"]
    if yt["daily_search_calls"] > 100 or yt["daily_other_units"] > 10000:
        raise ValueError("Le budget dépasse les allocations gratuites par défaut vérifiées.")
    if not 1 <= yt["baseline_videos"] <= 50 or yt["min_baseline"] < 3 or yt["channels_per_run"] > 20:
        raise ValueError("Historique : 3 références minimum, 1..50 vidéos et 20 chaînes maximum.")
    for name in value["reddit_communities"]:
        if not re.fullmatch(r"[A-Za-z0-9_]{1,40}", name):
            raise ValueError("Communauté Reddit invalide.")
    if not isinstance(value["topic_aliases"], dict) or any(not isinstance(name, str) or not name.strip() or not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases) for name, aliases in value["topic_aliases"].items()):
        raise ValueError("Alias : objet associant un sujet à une liste de variantes non vides requis.")
    for field in ("allowed_categories", "excluded_categories"):
        if not isinstance(value[field], list) or set(value[field]) - {"ai-tech", "general", "sensitive"}:
            raise ValueError("Catégories prises en charge : ai-tech, general, sensitive.")
    if type(value["elevenlabs"]["enabled"]) is not bool:
        raise ValueError("Activation ElevenLabs booléenne requise.")
    if value["elevenlabs"]["model_id"] != "eleven_multilingual_v2":
        raise ValueError("Seul le modèle à coût connu de 1 crédit/caractère est pris en charge.")
    if type(value["elevenlabs"]["max_characters"]) is not int or not 1 <= value["elevenlabs"]["max_characters"] <= 5000:
        raise ValueError("Plafond ElevenLabs 1..5000 caractères requis.")
    return value


def signal(source, title, url, published_at, observed_at, **extra):
    if not title or not url.startswith("https://"):
        raise ValueError("Titre et source HTTPS requis.")
    identifier = key([source, plain(title), extra.get("region")]) if source == "trends" else key([source, url])
    return {"id": identifier, "source": source, "title": " ".join(title.split()), "url": url,
            "published_at": stamp(published_at) if published_at else None, "observed_at": stamp(observed_at),
            "metrics": {}, "region": None, "language": None, **extra}
