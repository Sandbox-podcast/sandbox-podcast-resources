"""Render reviewed, platform-specific Shorts from any owned Sandbox episode. No publishing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from .identity import validate_video_id
from .rendering import render_pack, validate_render_pack
from .shorts import _sha256
from .storage import digest, exclusive_run, save_json

PLATFORMS = {"youtube", "tiktok", "instagram", "x"}


def build_packs(plan: object) -> list[dict]:
    """Validate every variant before allowing any file or process side effect."""
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("Plan social version 1 requis.")
    video_id = plan.get("video_id")
    if not isinstance(video_id, str):
        raise ValueError("video_id requis.")
    validate_video_id(video_id)
    clips = plan.get("clips")
    if not isinstance(clips, list) or not 1 <= len(clips) <= 100:
        raise ValueError("Entre 1 et 100 passages sont requis ; aucun quota de rendu imposé.")
    packs, identities = [], set()
    for clip in clips:
        if not isinstance(clip, dict) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", str(clip.get("id", ""))):
            raise ValueError("Identifiant de passage invalide.")
        if clip["id"] in identities:
            raise ValueError("Identifiant de passage dupliqué.")
        identities.add(clip["id"])
        variants = clip.get("variants")
        if not isinstance(variants, list) or not 1 <= len(variants) <= len(PLATFORMS):
            raise ValueError("Une à quatre variantes par passage sont requises.")
        platforms = set()
        for variant in variants:
            if (not isinstance(variant, dict) or not isinstance(variant.get("platform"), str)
                    or variant["platform"] not in PLATFORMS):
                raise ValueError("Réseau inconnu.")
            platform = variant["platform"]
            if platform in platforms:
                raise ValueError("Deux variantes du même réseau pour un passage.")
            platforms.add(platform)
            caption = variant.get("caption")
            if not isinstance(caption, str) or not caption.strip():
                raise ValueError("Légende propre au réseau requise.")
            start, end = variant.get("start"), variant.get("end")
            if any(isinstance(v, bool) or not isinstance(v, (float, int)) for v in (start, end)):
                raise ValueError("Bornes numériques requises.")
            candidate = {"id": digest({"video_id": video_id, "clip": clip["id"], "variant": variant})[:16],
                         "start": start, "end": end, "duration": end-start,
                         "title": variant.get("title"), "selected": True,
                         "layout": variant.get("layout", "fit")}
            pack = {"version": 1, "source_video_id": video_id,
                    "source_duration": plan.get("source_duration"), "candidates": [candidate]}
            validate_render_pack(pack)
            packs.append({"clip_id": clip["id"], "platform": platform,
                          "caption": caption, "pack": pack})
    return packs


def generate(plan: object, source: Path, transcript: Path, output: Path, *, execute: bool = False) -> dict:
    packs = build_packs(plan)
    source, transcript = source.resolve(strict=True), transcript.resolve(strict=True)
    output = output.resolve()
    if any(path.is_relative_to(output) for path in (source, transcript)):
        raise ValueError("Les sources doivent rester hors du dossier de sortie.")
    summary = {"video_id": plan["video_id"], "variants": len(packs),
               "platforms": sorted({p["platform"] for p in packs}), "publication": "not_uploaded"}
    if not execute:
        return {**summary, "dry_run": True}
    provenance = {"plan": plan, "source_sha256": _sha256(source), "transcript_sha256": _sha256(transcript)}
    with exclusive_run(output):
        receipt = output / "source-plan.json"
        if receipt.exists():
            if json.loads(receipt.read_text(encoding="utf-8")) != provenance:
                raise ValueError("Plan ou source modifié : utilise un nouveau dossier de sortie.")
        elif any(path.name != "run.lock" for path in output.iterdir()):
            raise ValueError("Le dossier contient des fichiers sans provenance : utilise un dossier neuf.")
        save_json(receipt, provenance)
        results = []
        for entry in packs:
            target = output / entry["platform"] / entry["clip_id"]
            if not target.resolve().is_relative_to(output):
                raise ValueError("La destination de la variante sort du dossier de sortie.")
            manifest = target / "render-manifest.json"
            pack = entry["pack"]
            expected = pack["candidates"][0]
            media = target / (expected["id"] + ".mp4")
            if manifest.exists():
                previous = json.loads(manifest.read_text(encoding="utf-8"))
                clips = previous.get("clips", [])
                if previous.get("source_sha256") != provenance["source_sha256"] or len(clips) != 1:
                    raise ValueError("Reçu de rendu incompatible : conserve le dossier pour vérification.")
                rendered = clips[0]
                if (any(rendered.get(key) != value for key, value in expected.items())
                        or rendered.get("technical_status") != "decoded"
                        or not media.is_file() or _sha256(media) != rendered.get("render_sha256")):
                    raise ValueError("Rendu modifié ou incomplet : aucun écrasement automatique.")
            else:
                if target.exists():
                    raise ValueError("Rendu interrompu sans reçu : conserve-le et choisis un nouveau dossier.")
                target.mkdir(parents=True)
                save_json(target / "native-pack.json", pack)
                rendered = render_pack(source, transcript, target / "native-pack.json", target)["clips"][0]
            (target / "caption.txt").write_text(entry["caption"] + "\n", encoding="utf-8")
            results.append({"clip_id": entry["clip_id"], "platform": entry["platform"],
                            "file": str(media),
                            "render_sha256": rendered["render_sha256"], "status": "needs_review"})
            save_json(output / "social-manifest.json", {**summary, "results": results, "complete": len(results) == len(packs)})
    return {**summary, "dry_run": False, "status": "needs_review"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="Lance les rendus locaux ; sinon simulation sans écriture.")
    args = parser.parse_args()
    try:
        result = generate(json.loads(args.plan.read_text(encoding="utf-8-sig")), args.source, args.transcript,
                          args.output, execute=args.execute)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
