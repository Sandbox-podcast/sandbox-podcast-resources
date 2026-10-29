"""Versioned local handoff files, kept consistent with reviewed packaging."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from .contracts import digest
from .media import fingerprint
from .packaging import revision


def export_pack(pack: dict, asset: dict, episode: dict, root: Path, *, proposed_at=None, valid_until=None) -> dict:
    pack = {**pack, "local_export_version": 1, "proposed_at": proposed_at,
            "embargo_at": episode.get("available_at") or episode.get("planned_publication_at"),
            "valid_until": valid_until or episode.get("next_filming_at"),
            "conditional_on_episode_availability": episode.get("availability") != "available"}
    pack.pop("updated_at", None)  # SQLite bookkeeping is not exported content.
    review=pack.get('local_packaging_review',{}).get('evidence',{})
    review_identity={'independent_review_sha256':review['sha256']} if review.get('sha256') else {}
    key = digest({"version": 1, "content": revision(pack), "asset": asset["sha256"], **review_identity,
                  "packaging_version": pack.get("local_packaging_version"), "run": pack.get("local_run_key"),
                  **{k: pack[k] for k in ("proposed_at", "embargo_at", "valid_until", "conditional_on_episode_availability")}})
    directory = root / pack["platform"] / pack["id"] / key[:24]
    directory.mkdir(parents=True, exist_ok=True)
    pack["pack_path"] = str(directory / "pack.json")
    if pack["platform"] == "linkedin":
        for source, name, sha in ((asset["path"], "video.mp4", asset["sha256"]), (pack["cover"], "cover.jpg", pack["cover_sha256"])):
            target = directory / name
            if fingerprint(Path(source)) != sha:
                raise ValueError("Fichier local modifié avant export du pack.")
            if not target.exists():shutil.copy2(source,target)
            if fingerprint(target) != sha:
                raise ValueError("Copie du pack local modifiée ; conserver la version pour diagnostic.")
        pack["manual_pack"] = str(directory)
        pack["manual_video_path"] = str(directory / "video.mp4")
        pack["manual_cover_path"] = str(directory / "cover.jpg")
    files = {"pack.json": json.dumps(pack, ensure_ascii=False, allow_nan=False, indent=2)+"\n",
             "texte.txt": pack["text"]+"\n\n"+pack["cta"]+"\n"}
    for name, content in files.items():
        target = directory / name
        if target.exists() and target.read_text(encoding="utf-8") != content:
            raise ValueError("Le pack exporté existe avec un autre contenu ; aucun écrasement.")
        if not target.exists():target.write_text(content, encoding="utf-8")
    return pack


def verify_pack(pack: dict, asset: dict):
    if pack.get("local_export_version") != 1:
        raise ValueError("Version du pack local à régénérer.")
    manifest = json.loads(Path(pack["pack_path"]).read_text(encoding="utf-8"))
    if manifest != {k:v for k,v in pack.items() if k != "updated_at"}:
        raise ValueError("Le manifeste du pack local diffère de l'état courant.")
    directory = Path(pack["pack_path"]).parent
    if (directory / "texte.txt").read_text(encoding="utf-8") != pack["text"]+"\n\n"+pack["cta"]+"\n":
        raise ValueError("Texte du pack local modifié.")
    if pack["platform"] == "linkedin":
        if (Path(pack["manual_pack"]) != directory or fingerprint(directory / "video.mp4") != asset["sha256"]
                or fingerprint(directory / "cover.jpg") != pack["cover_sha256"]):
            raise ValueError("Médias du pack LinkedIn modifiés ou incohérents.")
