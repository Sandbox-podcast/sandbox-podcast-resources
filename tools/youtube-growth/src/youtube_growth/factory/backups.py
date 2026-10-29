"""Instantanés SQLite vérifiés, médias portables et restauration en pause."""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import ntpath
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import sqlite3
import tempfile
from typing import Any

from .contracts import iso, utcnow
from .store import Store


KIND = "sandbox_factory_snapshot"
VERSION = 2
_HEX = re.compile(r"[a-f0-9]{64}")
_PRIVATE_NAMES = {"credentials.json", "token.json", "youtube-token.json", "id_rsa", "id_ed25519"}
_PRIVATE_KEYS = {"access_token", "refresh_token", "client_secret", "api_key", "private_key"}


def _sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _load(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("Objet JSON de sauvegarde requis.")
    return result


def _safe_relative(value: Any) -> Path:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or value.startswith("/") or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("Chemin relatif de sauvegarde invalide.")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or parsed.as_posix() != value:
        raise ValueError("Chemin de sauvegarde non canonique.")
    return Path(*parsed.parts)


def _under(root: Path, relative: Any) -> Path:
    result = root / _safe_relative(relative)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("Un fichier sort du périmètre de sauvegarde.")
    return result


def _secret_payload(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).lower() in _PRIVATE_KEYS or _secret_payload(item) for key, item in value.items())
    return isinstance(value, list) and any(_secret_payload(item) for item in value)


def _assert_business_file(path: Path) -> None:
    """Les configs globales ne sont jamais parcourues ; refuser les secrets usuels."""
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise ValueError("Liens de fichiers et jonctions exclus des sauvegardes portables.")
    lower = path.name.lower()
    if lower in _PRIVATE_NAMES or lower.startswith((".env", "client_secret")) or path.suffix.lower() in {".pem", ".key"}:
        raise ValueError("Un fichier de credentials ne peut entrer dans une sauvegarde média.")
    if path.suffix.lower() == ".json":
        try:
            content = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError):
            return
        if _secret_payload(content):
            raise ValueError("Un artefact contient des credentials ; sauvegarde refusée.")


def _check_database(path: Path) -> list[dict]:
    try:
        with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("La base de sauvegarde est invalide.")
            for table, column in (("records", "data"), ("publications", "data"), ("jobs", "payload"),
                                   ("events", "data"), ("settings", "value")):
                if any(_secret_payload(json.loads(row[0])) for row in connection.execute(f"SELECT {column} FROM {table}")):
                    raise ValueError("Des credentials sont présents dans l'état ; sauvegarde refusée.")
            if any(str(row[0]).lower() in _PRIVATE_KEYS | {"credentials", "token"}
                   for row in connection.execute("SELECT key FROM settings")):
                raise ValueError("Une configuration secrète est présente dans l'état.")
            return [{"kind": row[0], "id": row[1], "episode_id": row[2], "data": json.loads(row[3])}
                    for row in connection.execute("SELECT kind,id,episode_id,data FROM records")]
    except sqlite3.DatabaseError as error:
        raise ValueError("La base de sauvegarde est illisible ou incomplète.") from error


def _episode_id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value):
        raise ValueError("Identifiant d'épisode invalide dans la sauvegarde.")
    return value


def _registered_files(record: dict):
    """Yield durable file references and their recorded byte hashes when present."""
    row = record["data"]
    if record["kind"] in {"episode", "episode_revision"}:
        for name in ("source", "transcript", "evidence"):
            if row.get(name):
                yield row[name], name, row.get("source_sha256") if name == "source" else None
    elif record["kind"] == "asset":
        for name, hash_name in (("path", "sha256"), ("master_path", "master_sha256"),
                                ("subtitle_path", "subtitle_sha256"), ("ass_path", "ass_sha256")):
            if row.get(name):
                yield row[name], "asset-"+name, row.get(hash_name)
    elif record["kind"] == "thumbnail_bundle":
        for artifact in row.get("artifacts", []):
            yield artifact["path"], "thumbnail-"+artifact["kind"], artifact["sha256"]
        # brief_sha256 is a semantic hash, not the bytes of the JSON file.
        for name in ("brief_path", "receipt_path"):
            if row.get(name):
                yield row[name], "thumbnail-"+name, None
    elif record["kind"] == "research":
        for source in row.get("sources", []):
            yield source["snapshot"], "research-source", source["sha256"]
    elif record["kind"] == "narrative":
        for artifact in row.get("inputs", [])+(row.get("asset") or {}).get("artifacts", []):
            yield artifact["path"], "narrative-artifact", artifact["sha256"]
        for stage in row.get("stages", {}).values():
            yield stage["receipt"], "narrative-receipt", stage.get("sha256")


def _inventory(records: list[dict], state: Path) -> list[dict]:
    entries: dict[str, dict] = {}
    destinations: dict[str, str] = {}
    def add(raw: str, relative: str | None, *, role: str, episode_id: str | None, expected=None):
        source = Path(raw)
        if not source.is_absolute():
            raise ValueError("Référence média absolue requise dans l'état persistant.")
        _assert_business_file(source)
        source = source.resolve(strict=True)
        if not source.is_file():
            raise ValueError("Un média référencé n'est pas un fichier.")
        sha = _sha(source)
        if expected is not None and sha != expected:
            raise ValueError("Un média a changé depuis son enregistrement ; sauvegarde refusée.")
        if str(source) in entries:
            return
        if any(source.is_relative_to(state / folder) for folder in ("episodes", "narratives", "narrative-cache", "editorial", "story-design", "research-sources")):
            relative = source.relative_to(state).as_posix()
        elif relative is None:
            identity = _episode_id(episode_id or "research")
            suffix = source.suffix.lower()
            relative = f"sources/{identity}/{role}-{sha[:16]}{suffix}"
        _safe_relative(relative)
        if relative in destinations and destinations[relative] != str(source):
            raise ValueError("Deux médias partagent une destination de sauvegarde.")
        destinations[relative] = str(source)
        entries[str(source)] = {"relative_path": relative, "original_path": str(source), "sha256": sha,
                                "size_bytes": source.stat().st_size, "role": role, "episode_id": episode_id}
    for folder in ("episodes", "narratives", "narrative-cache", "editorial", "story-design", "research-sources"):
        episodes = state / folder
        if not episodes.exists():
            continue
        if not episodes.resolve().is_relative_to(state):
            raise ValueError("Le dossier des épisodes sort du stockage de la factory.")
        for path in sorted(episodes.rglob("*")):
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise ValueError("Jonction ou lien dans les artefacts d'épisode.")
            if path.is_file() and path.name not in {"run.lock"} and not path.name.endswith(".lock"):
                add(str(path), path.relative_to(state).as_posix(), role="factory_artifact", episode_id=None)
    for record in records:
        for path, role, expected in _registered_files(record):
            add(path, None, role=role, episode_id=record["data"].get("episode_id", record["episode_id"]), expected=expected)
    return sorted(entries.values(), key=lambda row: row["relative_path"])


def _copy_verified(source: Path, target: Path, expected: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, target.open("xb") as destination:
        shutil.copyfileobj(original, destination, length=1024 * 1024)
    if _sha(target) != expected:
        raise ValueError("Empreinte différente pendant la copie ; instantané incomplet.")
    shutil.copystat(source, target)


def backup(store: Store, target: Path, include_media: bool = False) -> dict:
    target = Path(target).resolve()
    manifest, payload = target.with_suffix(".manifest.json"), target.with_suffix(".media")
    if type(include_media) is not bool:
        raise ValueError("include_media doit être un booléen.")
    if len({target, manifest, payload}) != 3 or any(path.exists() for path in (target, manifest, payload)) or target == store.path:
        raise ValueError("La sauvegarde exige une destination et des fichiers annexes neufs.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".factory-snapshot-", dir=target.parent) as temporary:
        consistent = Path(temporary) / "database.sqlite3"
        # Use the existing SQLite backup API, not a copy of a live WAL database.
        store.backup(consistent)
        records = _check_database(consistent)
        entries = _inventory(records, store.directory) if include_media else []
        database_sha = _sha(consistent)
        # All files were checked before creating the final payload. Each copy is
        # checked again so a concurrent source write cannot yield a valid receipt.
        if include_media:
            payload.mkdir(exist_ok=False)
            for row in entries:
                _copy_verified(Path(row["original_path"]), _under(payload, row["relative_path"]), row["sha256"])
        _copy_verified(consistent, target, database_sha)
        result = {"version": VERSION, "kind": KIND, "database": target.name, "database_sha256": database_sha,
                  "created_at": iso(utcnow()), "origin_state_directory": str(store.directory),
                  "include_media": include_media, "portable": include_media,
                  "media_directory": payload.name if include_media else None, "files": entries,
                  "media": [{"path": row["data"].get("path"), "sha256": row["data"].get("sha256")}
                            for row in records if row["kind"] == "asset"]}
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return {**result, "snapshot": str(target), "manifest": str(manifest),
            "media_backup": str(payload) if include_media else None}


def _path_key(value: str) -> tuple[str, str] | None:
    if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("\\\\"):
        return "windows", ntpath.normcase(ntpath.normpath(value))
    if value.startswith("/"):
        return "posix", str(PurePosixPath(value))
    return None


def _remapper(origin: str, target: Path, files: list[dict]):
    old = _path_key(origin)
    if old is None:
        raise ValueError("Dossier d'origine absolu requis.")
    exact = {_path_key(row["original_path"]): str(_under(target, row["relative_path"])) for row in files}
    def remap(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: remap(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remap(item) for item in value]
        if not isinstance(value, str):
            return value
        current = _path_key(value)
        if current in exact:
            return exact[current]
        if current and current[0] == old[0]:
            separator = "\\" if old[0] == "windows" else "/"
            if current[1] == old[1]:
                return str(target)
            if current[1].startswith(old[1].rstrip(separator)+separator):
                relative = (PureWindowsPath(value).relative_to(PureWindowsPath(origin)) if old[0] == "windows"
                            else PurePosixPath(value).relative_to(PurePosixPath(origin)))
                return str(_under(target, relative.as_posix()))
        return value
    return remap


def _validate_receipt(snapshot: Path) -> tuple[dict, Path]:
    receipt = _load(snapshot.with_suffix(".manifest.json"))
    if (receipt.get("version") != VERSION or receipt.get("kind") != KIND or receipt.get("database") != snapshot.name
            or not isinstance(receipt.get("database_sha256"), str) or not _HEX.fullmatch(receipt["database_sha256"])):
        raise ValueError("Reçu de sauvegarde portable invalide ou ancien format non pris en charge.")
    if _sha(snapshot) != receipt["database_sha256"]:
        raise ValueError("Empreinte de base de sauvegarde invalide.")
    records = _check_database(snapshot)
    if type(receipt.get("include_media")) is not bool or receipt.get("portable") != receipt["include_media"]:
        raise ValueError("État de portabilité incohérent.")
    files = receipt.get("files")
    if not isinstance(files, list):
        raise ValueError("Inventaire des fichiers requis.")
    payload = snapshot.with_suffix(".media")
    if not receipt["include_media"]:
        if files or receipt.get("media_directory") is not None:
            raise ValueError("Inventaire média incohérent.")
        return receipt, payload
    if (receipt.get("media_directory") != payload.name or payload.is_symlink() or not payload.is_dir()
            or (hasattr(payload, "is_junction") and payload.is_junction())):
        raise ValueError("Dossier média de sauvegarde invalide.")
    originals, destinations = set(), set()
    for row in files:
        if not isinstance(row, dict) or not isinstance(row.get("original_path"), str) or _path_key(row["original_path"]) is None:
            raise ValueError("Origine de fichier absolue requise.")
        relative = row.get("relative_path")
        if _safe_relative(relative).parts[0] not in {"episodes", "sources", "narratives", "narrative-cache", "editorial", "story-design", "research-sources"}:
            raise ValueError("Le média n'appartient pas aux épisodes ou à leurs sources.")
        source = _under(payload, relative)
        if relative in destinations or _path_key(row["original_path"]) in originals:
            raise ValueError("Entrée de sauvegarde dupliquée.")
        destinations.add(relative)
        originals.add(_path_key(row["original_path"]))
        if (not isinstance(row.get("sha256"), str) or not _HEX.fullmatch(row["sha256"])
                or type(row.get("size_bytes")) is not int or row["size_bytes"] < 0):
            raise ValueError("Empreinte ou taille média invalide.")
        _assert_business_file(source)
        if not source.is_file() or source.stat().st_size != row["size_bytes"] or _sha(source) != row["sha256"]:
            raise ValueError("Un média de sauvegarde manque ou son empreinte a changé.")
    if any(parent.as_posix() in destinations for relative in destinations
           for parent in PurePosixPath(relative).parents if parent.as_posix() != "."):
        raise ValueError("Un fichier de sauvegarde est aussi déclaré comme dossier.")
    by_original = {_path_key(row["original_path"]): row for row in files}
    for record in records:
        for path, _, expected in _registered_files(record):
            entry = by_original.get(_path_key(path))
            if entry is None:
                raise ValueError("Un média référencé dans la base est absent de l'inventaire portable.")
            if expected is not None and entry["sha256"] != expected:
                raise ValueError("L'empreinte de l'inventaire diffère du média enregistré dans la base.")
    return receipt, payload


def restore(snapshot: Path, directory: Path) -> dict:
    snapshot = Path(snapshot).resolve(strict=True)
    directory = Path(directory).resolve()
    if directory.exists():
        raise ValueError("La restauration exige un dossier neuf et absent.")
    # Validate the database, every path and every media hash before creating output.
    receipt, payload = _validate_receipt(snapshot)
    remap = _remapper(receipt["origin_state_directory"], directory, receipt["files"])
    directory.mkdir(parents=True, exist_ok=False)
    _copy_verified(snapshot, directory / "factory.sqlite3", receipt["database_sha256"])
    changed = []
    for row in receipt["files"]:
        target = _under(directory, row["relative_path"])
        _copy_verified(_under(payload, row["relative_path"]), target, row["sha256"])
        if target.suffix.lower() == ".json":
            try:
                before = json.loads(target.read_text(encoding="utf-8-sig"))
            except (UnicodeError, json.JSONDecodeError):
                continue
            after = remap(before)
            if isinstance(after, dict) and {"identity", "payload", "payload_sha256"} <= after.keys():
                from .contracts import digest
                after["payload_sha256"] = digest(after["payload"])
            if before != after:
                target.write_text(json.dumps(after, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
                changed.append({"relative_path": row["relative_path"], "previous_sha256": row["sha256"], "new_sha256": _sha(target)})
    with Store(directory) as store:
        with store.transaction():
            changed_by_path = {str(_under(directory, row["relative_path"])): row["new_sha256"] for row in changed}
            def refresh_hashes(value):
                if isinstance(value, list):
                    return [refresh_hashes(item) for item in value]
                if not isinstance(value, dict):
                    return value
                result = {key: refresh_hashes(item) for key,item in value.items()}
                for name in ("path", "receipt"):
                    if isinstance(result.get(name), str) and result[name] in changed_by_path and "sha256" in result:
                        result["sha256"] = changed_by_path[result[name]]
                return result
            for table, key, column in (("records", "rowid", "data"), ("publications", "id", "data"),
                                       ("jobs", "id", "payload"), ("events", "sequence", "data")):
                for identity, value in store.db.execute(f"SELECT {key},{column} FROM {table}").fetchall():
                    updated = refresh_hashes(remap(json.loads(value)))
                    if table == "records" and updated.get("story_id") and updated.get("stages"):
                        from .contracts import digest
                        updated["review_revision"] = digest({"stages": {k:v["sha256"] for k,v in updated["stages"].items()},
                                                               "asset_sha256": (updated.get("asset") or {}).get("sha256")})
                        if updated.get("review"):
                            updated["previous_review"] = updated.pop("review")
                        updated["human_content_validation"] = "pending"
                    store.db.execute(f"UPDATE {table} SET {column}=? WHERE {key}=?",
                                     (json.dumps(updated, ensure_ascii=False, allow_nan=False), identity))
            # A restored process owns no old lease. Never replay an interrupted send.
            store.db.execute("UPDATE publications SET status='unknown' WHERE status='sending'")
            store.db.execute("UPDATE jobs SET status=CASE WHEN kind='dispatch' THEN 'unknown' ELSE 'queued' END,owner=NULL,lease_until=NULL WHERE status='running'")
            store.set_setting("paused", True)
            store.set_setting("heartbeat", None)
            store.event("snapshot_restored", None, {"source_sha256": receipt["database_sha256"], "paused": True,
                        "portable": receipt["include_media"], "json_files_remapped": changed})
    result = {"status": "restored_paused", "database": str(directory / "factory.sqlite3"),
              "portable": receipt["include_media"], "media_files": len(receipt["files"]),
              "json_files_remapped": changed, "source_database_sha256": receipt["database_sha256"],
              "media_inventory": receipt["media"], "media_location": str(directory),
              "limitations": [] if receipt["include_media"] else ["database_only_media_not_restored"]}
    (directory / "restore-receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return result
