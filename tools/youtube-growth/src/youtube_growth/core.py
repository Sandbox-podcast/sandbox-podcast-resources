from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SENSITIVE_COMMENT_PATTERNS = (
    re.compile(r"\b(suicid\w*|automutil\w*|me tuer|me faire du mal|self[- ]harm|suicid\w*)\b", re.I),
    re.compile(r"\b(avocat|procès|poursuivre|diagnostic|médicament|médical|medical|diagnos\w*|legal advice)\b", re.I),
    re.compile(r"\b(menace|menacer|tuer|kill you|death threat|terroris\w*)\b", re.I),
    re.compile(r"\b(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+?\d[\d .()/-]{7,}\d)\b"),
)


@dataclass(slots=True)
class State:
    last_video_id: str | None = None
    comments_baselined: bool = False
    pending_video_ids: list[str] = field(default_factory=list)
    posted_episode_comments: list[str] = field(default_factory=list)
    seen_comment_ids: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> State:
        if not path.exists():
            return cls()
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: object) -> State:
        if not isinstance(raw, dict):
            raise ValueError("Le fichier d'état YouTube doit contenir un objet JSON.")
        known = {key: raw.get(key, default) for key, default in asdict(cls()).items()}
        if any(value is not None and not isinstance(value, str) for value in [known["last_video_id"]]):
            raise ValueError("last_video_id doit être une chaîne ou null.")
        if not isinstance(known["comments_baselined"], bool):
            raise ValueError("comments_baselined doit être un booléen.")
        for key in ("pending_video_ids", "posted_episode_comments", "seen_comment_ids"):
            if not isinstance(known[key], list) or any(not isinstance(item, str) for item in known[key]):
                raise ValueError(f"{key} doit être une liste de chaînes.")
        return cls(**known)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)


@dataclass(frozen=True, slots=True)
class ReplyDecision:
    publish: bool
    reply: str
    reason: str


def find_new_uploads(video_ids_newest_first: list[str], last_video_id: str | None) -> list[str] | None:
    """Retourne les nouveaux identifiants dans l'ordre chronologique, ou None si le curseur a disparu."""
    if not video_ids_newest_first:
        return []
    if last_video_id is None:
        return []
    try:
        cursor_index = video_ids_newest_first.index(last_video_id)
    except ValueError:
        return None
    return list(reversed(video_ids_newest_first[:cursor_index]))


def comment_needs_human_review(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_COMMENT_PATTERNS)


def parse_reply_decision(text: str) -> ReplyDecision:
    """Analyse une décision JSON d'IA. Toute sortie non conforme est ignorée par défaut."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return ReplyDecision(False, "", "Réponse du modèle invalide; revue humaine requise.")
    if not isinstance(value, dict):
        return ReplyDecision(False, "", "Réponse du modèle invalide; revue humaine requise.")
    publish = value.get("publish") is True
    reply = value.get("reply") if isinstance(value.get("reply"), str) else ""
    reason = value.get("reason") if isinstance(value.get("reason"), str) else "Motif absent."
    if not reply.strip() or len(reply) > 900:
        return ReplyDecision(False, "", "Réponse vide ou trop longue; revue humaine requise.")
    if any(ord(character) < 32 and character not in "\n\t" for character in reply):
        return ReplyDecision(False, "", "Réponse avec caractères de contrôle; revue humaine requise.")
    return ReplyDecision(publish, reply.strip(), reason[:240])
