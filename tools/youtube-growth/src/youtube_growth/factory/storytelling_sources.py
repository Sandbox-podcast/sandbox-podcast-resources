"""Import user-selected material into immutable local snapshots."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from urllib.parse import parse_qsl, urlsplit
from urllib.error import URLError
import xml.etree.ElementTree as ET
import zipfile

from .contracts import digest, iso, load_json, utcnow
from .media import fingerprint
from .research import fetch_sources

TEXT_LIMIT = 2_000_000
DOCUMENT_LIMIT = 25_000_000
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}


def _freeze(raw, output, suffix):
    key = hashlib.sha256(raw).hexdigest()
    path = output / (key + suffix)
    if path.exists():
        if fingerprint(path) != key:
            raise ValueError("imported_snapshot_changed")
    else:
        with path.open("xb") as stream:
            stream.write(raw)
    return path, key


def _copy(path, output):
    before = path.stat()
    key = fingerprint(path)
    target = output / (key + path.suffix.lower())
    if target.exists():
        if fingerprint(target) != key:
            raise ValueError("imported_snapshot_changed")
    else:
        # Exclusive creation also protects against replacing a source or a concurrent import.
        try:
            with path.open("rb") as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
        except FileExistsError:
            pass
        if fingerprint(target) != key:
            raise ValueError("source_changed_during_import")
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError("source_changed_during_import")
    return target, key


def _extract(path):
    suffix = path.suffix.lower()
    if path.stat().st_size > DOCUMENT_LIMIT:
        raise ValueError("document_too_large")
    if suffix in {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8-sig")
    elif suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            if sum(item.file_size for item in archive.infolist()) > DOCUMENT_LIMIT:
                raise ValueError("docx_uncompressed_too_large")
            root = ET.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        text = "\n".join("".join(item.text or "" for item in paragraph.findall(".//w:t", ns))
                         for paragraph in root.findall(".//w:p", ns))
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("pdf_text_extractor_missing_install_pypdf") from None
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise ValueError("encrypted_pdf_requires_text_export")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        raise ValueError("document_format_not_supported_export_utf8_text")
    if not text.strip():
        raise ValueError("document_has_no_text_use_ocr_or_text_export")
    if len(text) > TEXT_LIMIT:
        raise ValueError("document_text_too_large")
    return text


def import_sources(brief, directory: Path):
    """Only explicit links/files are read; content is never followed as instructions."""
    if not isinstance(brief, dict):
        raise ValueError("Brief objet requis pour importer les sources.")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    raw_dir, text_dir = directory / "originals", directory / "texts"
    raw_dir.mkdir(exist_ok=True)
    text_dir.mkdir(exist_ok=True)
    sources, artifacts, blockers, seen = [], [], [], set()
    metadata = brief.get("source_metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("source_metadata doit être un objet indexé par référence.")
    media_rights = brief.get("media_rights", {})
    if not isinstance(media_rights, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k, v in media_rights.items()):
        raise ValueError("media_rights doit associer chaque chemin à ses droits d'usage.")

    def add(source):
        if source["source_id"] in seen:
            return
        seen.add(source["source_id"])
        source["instruction_policy"] = "untrusted_data_never_system_instructions"
        source["verification_status"] = "unverified_import"
        sources.append(source)
        for path_field, hash_field in (("path", "sha256"), ("text_path", "text_sha256")):
            if source.get(path_field):
                artifact = {"path": source[path_field], "sha256": source[hash_field]}
                if artifact not in artifacts:
                    artifacts.append(artifact)

    notes = brief.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("Les notes doivent être du texte.")
    if notes.strip():
        if len(notes) > TEXT_LIMIT:
            raise ValueError("notes_too_large")
        path, sha = _freeze(notes.encode("utf-8"), text_dir, ".txt")
        add({"source_id": "notes", "title": "Notes fournies", "kind": "user_notes", "text": notes,
             "path": str(path), "sha256": sha, "rights": "user_supplied_for_project", "media_type": "text"})
    for field in ("documents", "media"):
        refs = brief.get(field, [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError(f"Liste de chemins explicites requise : {field}.")
        for ref in refs:
            path = Path(ref).expanduser().resolve()
            key = "source-" + digest(str(path))[:20]
            meta = metadata.get(ref, {})
            if not isinstance(meta, dict):
                raise ValueError("Métadonnées de source objet requises.")
            try:
                if not path.is_file():
                    raise ValueError("source_file_missing")
                # File inputs are explicitly chosen by the user; model output cannot add paths.
                frozen, sha = _copy(path, raw_dir)
                suffix = path.suffix.lower()
                media_type = "image" if suffix in IMAGE_EXTENSIONS else "video" if suffix in VIDEO_EXTENSIONS else "audio" if suffix in AUDIO_EXTENSIONS else "text"
                source = {"source_id": key, "title": meta.get("title", path.name), "kind": meta.get("kind", "user_document"),
                          "original_reference": str(path), "path": str(frozen), "sha256": sha,
                          "rights": meta.get("rights", media_rights.get(ref, "usage_to_confirm" if media_type != "text" else "user_supplied_for_project")),
                          "generated": meta.get("generated", False), "media_type": media_type,
                          "text": "", "retrieved_at": iso(utcnow())}
                if isinstance(meta.get("verification"), dict):
                    source["verification"] = meta["verification"]
                if media_type == "text":
                    content = _extract(frozen)
                    snapshot, text_sha = _freeze(content.encode("utf-8"), text_dir, ".txt")
                    source.update(text=content, text_path=str(snapshot), text_sha256=text_sha)
                add(source)
            except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
                code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "source_import_failed"
                blockers.append({"source_id": key, "reference": ref, "code": code,
                                 "action": "Vérifier le chemin, le format et les droits ; importer une copie texte si nécessaire."})
    links = brief.get("links", [])
    if not isinstance(links, list) or any(not isinstance(ref, str) or not ref.strip() for ref in links):
        raise ValueError("Liste d'URL explicites requise.")
    for url in dict.fromkeys(links):
        key = "source-" + digest(url)[:20]
        meta = metadata.get(url, {})
        if not isinstance(meta, dict):
            raise ValueError("Métadonnées de source objet requises.")
        try:
            if any(name.casefold() in {"token", "key", "api_key", "secret", "access_token", "authorization"}
                   for name, _ in parse_qsl(urlsplit(url).query)):
                raise ValueError("source_url_credentials_forbidden")
            result = fetch_sources({"sources": [{"source_id": key, "title": meta.get("title", urlsplit(url).hostname or "Lien fourni"),
                                                  "url": url, "kind": meta.get("kind", "secondary"),
                                                  "rights": meta.get("rights", "citation_only")}]}, text_dir)
            imported = load_json(Path(result["dossier_path"]))["sources"][0]
            path = Path(imported["snapshot"])
            add({**imported, "path": str(path), "text": path.read_text(encoding="utf-8"), "media_type": "text",
                 **({"verification": meta["verification"]} if isinstance(meta.get("verification"), dict) else {})})
        except (OSError, ValueError, URLError) as error:
            code = str(error) if isinstance(error, ValueError) and str(error).replace("_", "").isalnum() else "source_link_unavailable"
            blockers.append({"source_id": key, "reference": url, "code": code,
                             "action": "Fournir une URL HTTPS publique ou importer une copie texte autorisée."})
    result = {"version": 1, "sources": sources, "artifacts": artifacts, "blockers": blockers,
              "research_discovery": "not_performed", "source_policy": "untrusted_data", "claims_verified": False}
    path = directory / ("sources-" + digest(result) + ".json")
    if not path.exists():
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["manifest_path"] = str(path)
    return result
