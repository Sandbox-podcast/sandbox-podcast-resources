"""Prepare text and manual packs from explicit reviewed editorial evidence."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from .contracts import PLATFORMS, digest


def revision(pack: dict) -> str:
    """Use content and hashes, so moving/restoring files preserves the review."""
    from .thumbnails import _portable
    return digest({"title": pack.get("title"), "text": pack.get("text"), "cta": pack.get("cta"),
                   "destination": pack.get("destination"), "asset_sha256": pack.get("asset_sha256"),
                   "cover_sha256": pack.get("cover_sha256"), "variants": _portable(pack.get("variants", [])),
                   "thumbnail_digest": pack.get("thumbnail_bundle", {}).get("content_digest")})


def assert_reviewed(pack: dict, asset: dict | None = None):
    required = pack.get("thumbnail_required") or (pack.get("platform") == "youtube" and (asset or {}).get("format") == "horizontal")
    if not required:
        return
    from .thumbnails import validate_bundle
    bundle = pack.get("thumbnail_bundle")
    if not isinstance(bundle, dict):
        raise ValueError("thumbnail_concepts_required")
    validate_bundle(bundle, asset=asset, require_review=True)
    selected = next((v for v in bundle["variants"] if v["concept_id"] == bundle["selected_concept_id"]), None)
    if not selected or pack.get("title") != selected["title"] or pack.get("cover_sha256") != selected["thumbnail"]["sha256"]:
        raise ValueError("selected_title_or_thumbnail_changed")
    from .media import fingerprint
    if not pack.get("cover") or fingerprint(Path(pack["cover"])) != pack["cover_sha256"]:
        raise ValueError("selected_thumbnail_file_changed")
    if pack.get("packaging_review", {}).get("revision") != revision(pack):
        raise ValueError("packaging_revision_requires_review")


def prepare(episode: dict, candidate: dict, asset: dict, config: dict, output: Path) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    requests = candidate.get("platforms", ["youtube"])
    if not isinstance(requests, list) or set(requests)-PLATFORMS:
        raise ValueError("Plateformes éditoriales invalides.")
    text_by_platform = candidate.get("packaging", {})
    results = []
    for platform in requests:
        explicit = text_by_platform.get(platform, {})
        title = explicit.get("title", candidate["title"])
        text = explicit.get("text", candidate.get("benefit", candidate.get("rationale", "")))
        destination = episode.get("full_episode_url")
        cta = explicit.get("cta", "Émission complète : "+destination if destination else "Lien de l'émission en attente.")
        variants = explicit.get("variants", [])
        if len(variants) > 3 or any(not all(v.get(k) for k in ("title", "hypothesis")) for v in variants):
            raise ValueError("Au plus trois variantes avec titre et hypothèse.")
        account = explicit.get("account_id")
        if platform != "linkedin" and not account:
            accounts = config["authorized_accounts"][platform]
            # A unique configured account is explicit configuration, not an inferred identity.
            account = accounts[0] if len(accounts) == 1 else "unconfigured"
        identity = digest({"episode": episode["episode_id"], "segment": candidate["segment_id"], "format": asset["format"], "platform": platform, "account": account or "manual"})[:24]
        pack = {"id": identity, "episode_id": episode["episode_id"], "segment_id": candidate["segment_id"],
                "asset_id": asset["asset_id"], "asset_sha256": asset["sha256"], "platform": platform,
                "account_id": account or "manual", "title": title, "text": text, "cta": cta,
                "destination": destination, "variants": variants, "status": "ready", "editorial_current": True, "qa_status": asset.get("qa_status", "needs_review"),
                "synthetic": episode.get("synthetic", False), "editorial_score": candidate.get("editorial_score", 0),
                "cover": asset.get("thumbnail"), "native_actions": []}
        pack["asset_format"] = asset["format"]
        pack["thumbnail_required"] = platform == "youtube" and asset["format"] == "horizontal"
        pack["packaging_status"] = "needs_thumbnail_concepts" if pack["thumbnail_required"] else "prepared"
        if platform == "youtube":
            pack["native_actions"] = ["Vérifier et ajouter la vidéo associée dans Studio pour un Short."] if asset["format"] == "vertical" else ["Vérifier les playlists, l'écran de fin natif et la disponibilité du test titres/miniatures dans Studio."]
        elif platform in {"x", "instagram", "tiktok"}:
            pack["native_actions"] = ["Vérifier les droits du compte, la couverture et les fonctions de lien disponibles."]
        revision = digest({"asset": asset["asset_id"], "sha256": asset["sha256"], "title": title, "text": text,
                           "cta": cta, "variants": variants, "destination": destination})[:20]
        directory = output / platform / identity / revision
        directory.mkdir(parents=True, exist_ok=True)
        pack["pack_path"] = str(directory / "pack.json")
        (directory / "texte.txt").write_text(text+"\n\n"+cta+"\n", encoding="utf-8")
        (directory / "pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        if platform == "linkedin":
            # Local export only. Never enqueue this pack in a connector.
            target = directory / "video.mp4"
            if not target.exists():
                shutil.copy2(asset["path"], target)
            from .media import fingerprint
            if fingerprint(target) != asset["sha256"]:
                raise ValueError("L'export LinkedIn a changé ; conserver la version pour diagnostic.")
            pack.update(manual_pack=str(directory), embargo_at=episode.get("available_at"), valid_until=episode.get("next_filming_at"))
            (directory / "pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(pack)
    return results
