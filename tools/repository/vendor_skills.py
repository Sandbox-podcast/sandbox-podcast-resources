"""Install pinned external skill collections, verify them and maintain their catalog.

Upstream files are read from Git objects and copied as data: no upstream script,
hook, plugin or server is executed or activated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = PurePosixPath(".agents/vendor")
LOCK = VENDOR / "skills-lock.json"
CATALOG = VENDOR / "catalog.json"
ROOT_FILES = {"README.md", "skills-lock.json", "catalog.json"}
TEXT_NAMES = {"LICENSE", "NOTICE"}
MAX_FILE_BYTES = 2_000_000
DESCRIPTION_LIMIT = 400


def pattern(glob):
    """Translate a POSIX glob with ** into an anchored regular expression."""
    result, index = "", 0
    while index < len(glob):
        if glob.startswith("**/", index):
            result, index = result + "(?:.*/)?", index + 3
        elif glob.startswith("**", index):
            result, index = result + ".*", index + 2
        elif glob[index] == "*":
            result, index = result + "[^/]*", index + 1
        elif glob[index] == "?":
            result, index = result + "[^/]", index + 1
        else:
            result, index = result + re.escape(glob[index]), index + 1
    return re.compile(result + r"\Z")


def selected(path, collection):
    """Map an upstream path to its installed path, or None when it is not requested."""
    if not any(pattern(glob).match(path) for glob in collection["include"]):
        return None
    if any(pattern(glob).match(path) for glob in collection.get("exclude", [])):
        return None
    for source, target in collection.get("map", {}).items():
        if path.startswith(source):
            return target + path[len(source):]
    return path


def safe_relative(path):
    value = PurePosixPath(path)
    if value.is_absolute() or not value.parts or any(part in {"", ".", ".."} or ":" in part for part in value.parts):
        raise ValueError("Chemin amont refusé : " + path)
    if value.suffix.lower() not in {".md", ".txt"} and value.name not in TEXT_NAMES:
        raise ValueError("Seuls les textes des skills et leurs licences sont installés : " + path)
    return value.as_posix()


def file_digest(content):
    # Hash normalized line endings so a Windows checkout and CI agree.
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def tree_summary(directory):
    # Order by POSIX path text: Windows sorts paths case-insensitively, Linux does not.
    rows = sorted((p.relative_to(directory).as_posix(), file_digest(p.read_bytes()))
                  for p in Path(directory).rglob("*") if p.is_file())
    names = [name for name, _ in rows]
    return {"files": len(rows),
            "tree_sha256": hashlib.sha256("".join(f"{n}\0{h}\n" for n, h in rows).encode("utf-8")).hexdigest(),
            "skills": sum(PurePosixPath(n).name == "SKILL.md" for n in names),
            "localized_skills": sum(n.startswith("skills/locales/") for n in names),
            "agents": sum(n.startswith("agents/") and n.endswith(".md") for n in names)}


def _git(arguments, *, binary=False):
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    process = subprocess.run(["git", "-c", "core.longpaths=true", "-c", "credential.helper=", *arguments],
                             capture_output=True, env=environment, timeout=600)
    if process.returncode:
        raise ValueError("Git a refusé la récupération : " + process.stderr.decode("utf-8", "replace").strip()[:500])
    return process.stdout if binary else process.stdout.decode("utf-8")


def fetch(collection):
    """Read requested blobs of the pinned commit without checking out the upstream tree."""
    with tempfile.TemporaryDirectory(prefix="vendor-skills-") as directory:
        _git(["init", "-q", directory])
        _git(["-C", directory, "fetch", "-q", "--depth", "1", "--no-tags", collection["repository"], collection["commit"]])
        if _git(["-C", directory, "rev-parse", "FETCH_HEAD"]).strip() != collection["commit"]:
            raise ValueError("Révision amont inattendue : " + collection["id"])
        result = {}
        for entry in _git(["-C", directory, "ls-tree", "-r", "-z", "--full-tree", "FETCH_HEAD"]).split("\0"):
            if not entry:
                continue
            meta, path = entry.split("\t", 1)
            mode, kind, sha = meta.split()
            target = selected(path, collection)
            if target is None:
                continue
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError("Entrée amont non textuelle refusée : " + path)
            result[safe_relative(target)] = _git(["-C", directory, "cat-file", "blob", sha], binary=True)
        return result


def load_lock(root=ROOT):
    value = json.loads((Path(root) / LOCK).read_text(encoding="utf-8"))
    if value.get("version") != 1 or not isinstance(value.get("collections"), list):
        raise ValueError("Verrou des collections invalide.")
    ids = [c.get("id") for c in value["collections"]]
    if len(set(ids)) != len(ids) or any(not isinstance(i, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", i) for i in ids):
        raise ValueError("Identifiants de collections invalides ou dupliqués.")
    for collection in value["collections"]:
        if not re.fullmatch(r"[0-9a-f]{40}", collection.get("commit", "")):
            raise ValueError("Révision complète requise : " + collection["id"])
        if not collection.get("include") or not collection.get("license_files"):
            raise ValueError("Fichiers inclus et licence requis : " + collection["id"])
    return value


def _write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def install(root=ROOT, *, only=None, replace_modified=False, fetcher=fetch):
    root = Path(root)
    lock = load_lock(root)
    unknown = set(only or ()) - {c["id"] for c in lock["collections"]}
    if unknown:
        raise ValueError("Collection inconnue : " + ", ".join(sorted(unknown)))
    for collection in lock["collections"]:
        if only and collection["id"] not in only:
            continue
        target = root / VENDOR / collection["id"]
        previous = collection.get("installed")
        if target.exists() and not replace_modified and (not previous or tree_summary(target)["tree_sha256"] != previous["tree_sha256"]):
            raise ValueError("Copie locale modifiée ou non suivie, conservée : " + str(target))
        files = fetcher(collection)
        for name in collection["license_files"]:
            if name not in files:
                raise ValueError("Licence absente de la sélection : " + collection["id"] + "/" + name)
        staging = root / VENDOR / (".staging-" + collection["id"])
        if staging.exists():
            shutil.rmtree(staging)
        for name, content in sorted(files.items()):
            if len(content) > MAX_FILE_BYTES:
                raise ValueError("Fichier amont trop volumineux : " + name)
            path = staging / safe_relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.replace(b"\r\n", b"\n"))
        if target.exists():
            shutil.rmtree(target)
        staging.rename(target)
        collection["installed"] = tree_summary(target)
    _write_json(root / LOCK, lock)
    _write_json(root / CATALOG, build_catalog(root, lock))
    return {c["id"]: c.get("installed") for c in lock["collections"]}


def frontmatter(text):
    match = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not match:
        return {}
    result, lines, index = {}, match.group(1).split("\n"), 0
    while index < len(lines):
        found = re.match(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", lines[index])
        index += 1
        if not found:
            continue
        key, value = found.groups()
        if value in {">", "|", ">-", "|-"}:
            block = []
            while index < len(lines) and (lines[index].startswith((" ", "\t")) or not lines[index].strip()):
                block.append(lines[index].strip())
                index += 1
            value = " ".join(part for part in block if part)
        elif value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                value = value.strip('"')
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        result[key] = value
    return result


def build_catalog(root, lock):
    entries = []
    for collection in lock["collections"]:
        base = Path(root) / VENDOR / collection["id"]
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            relative = path.relative_to(base).as_posix()
            parts = relative.split("/")
            if parts[0] == "agents":
                kind = "agent"
            elif parts[0] == "skills" and len(parts) > 1 and parts[1] == "locales":
                kind = "localized_skill"
            elif path.name == "SKILL.md":
                kind = "skill"
            else:
                continue
            meta = frontmatter(path.read_text(encoding="utf-8"))
            name = meta.get("name") or (path.parent.name if kind == "skill" else path.stem)
            language = meta.get("language") or (parts[2] if kind == "localized_skill" else collection.get("instructions_language", "en"))
            description = " ".join(str(meta.get("description", "")).split())
            if len(description) > DESCRIPTION_LIMIT:
                description = description[:DESCRIPTION_LIMIT - 1].rstrip() + "…"
            folder = PurePosixPath(relative).parent
            category = folder.parent if kind == "skill" else folder
            if kind == "localized_skill":
                category = PurePosixPath(*folder.parts[3:])
            entry = {"id": collection["id"] + "/" + name + ("@" + language if kind == "localized_skill" else ""),
                     "name": name, "collection": collection["id"], "kind": kind, "language": language,
                     "category": str(category).removeprefix("skills").strip("/") if kind != "agent" else "agents",
                     "path": (VENDOR / collection["id"] / relative).as_posix(), "description": description}
            entries.append(entry)
    ids = [e["id"] for e in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("Identifiants de skills dupliqués dans le catalogue.")
    return {"version": 1, "generated_by": "tools/repository/vendor_skills.py",
            "collections": {c["id"]: {"repository": c["repository"], "commit": c["commit"], "license": c["license"]}
                            for c in lock["collections"]},
            "entries": sorted(entries, key=lambda e: e["id"])}


def check(root=ROOT):
    root = Path(root)
    lock = load_lock(root)
    errors = []
    ids = {c["id"] for c in lock["collections"]}
    for item in (root / VENDOR).iterdir():
        if item.is_dir() and item.name not in ids:
            errors.append("Dossier sans collection verrouillée : " + item.name)
        elif item.is_file() and item.name not in ROOT_FILES:
            errors.append("Fichier inattendu : " + item.name)
    for collection in lock["collections"]:
        target = root / VENDOR / collection["id"]
        if not target.is_dir() or not collection.get("installed"):
            errors.append("Collection absente : " + collection["id"])
            continue
        if tree_summary(target) != collection["installed"]:
            errors.append("Contenu différent de la révision installée : " + collection["id"])
        errors.extend("Licence absente : " + collection["id"] + "/" + name
                      for name in collection["license_files"] if not (target / name).is_file())
    catalog_path = root / CATALOG
    if not catalog_path.is_file() or json.loads(catalog_path.read_text(encoding="utf-8")) != build_catalog(root, lock):
        errors.append("Catalogue à régénérer : python tools/repository/vendor_skills.py catalog")
    if errors:
        raise ValueError("Collections de skills incohérentes :\n" + "\n".join(errors))
    return {c["id"]: c["installed"] for c in lock["collections"]}


def find(root, query, *, language=None, collection=None):
    catalog = json.loads((Path(root) / CATALOG).read_text(encoding="utf-8"))
    words = [w.casefold() for w in query.split()]
    return [e for e in catalog["entries"]
            if all(w in " ".join((e["id"], e["category"], e["description"])).casefold() for w in words)
            and (not language or e["language"] == language) and (not collection or e["collection"] == collection)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    setup = commands.add_parser("install", help="Récupérer les révisions épinglées et réinstaller les collections.")
    setup.add_argument("--collection", action="append")
    setup.add_argument("--replace-modified", action="store_true")
    commands.add_parser("check", help="Vérifier le contenu installé, les licences et le catalogue (défaut).")
    commands.add_parser("catalog", help="Régénérer le catalogue depuis les fichiers installés vérifiés.")
    search = commands.add_parser("find", help="Chercher un skill dans le catalogue.")
    search.add_argument("query")
    search.add_argument("--language")
    search.add_argument("--collection")
    args = parser.parse_args(argv)
    if args.command == "install":
        result = install(only=args.collection, replace_modified=args.replace_modified)
    elif args.command == "catalog":
        lock = load_lock()
        for collection in lock["collections"]:
            if tree_summary(ROOT / VENDOR / collection["id"]) != collection.get("installed"):
                raise ValueError("Collection modifiée ; réinstaller avant le catalogue : " + collection["id"])
        _write_json(ROOT / CATALOG, build_catalog(ROOT, lock))
        result = {"catalog": CATALOG.as_posix()}
    elif args.command == "find":
        result = [{k: e[k] for k in ("id", "kind", "language", "path", "description")}
                  for e in find(ROOT, args.query, language=args.language, collection=args.collection)]
    else:
        result = check()
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
