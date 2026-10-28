"""Copy legacy local files to an ignored archive before changing checkout."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from check_repository import ROOT, local_only


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_files(root: Path, names: list[str], destination: Path, *, apply: bool) -> list[dict]:
    root, destination = root.resolve(), destination.resolve()
    if destination.is_relative_to(root) and not destination.is_relative_to(root / '.local'):
        raise ValueError('Une sauvegarde dans le dépôt doit rester sous .local/.')
    rows = []
    for name in sorted(set(names)):
        if not name or not local_only(name):
            continue
        source = root / name
        if source.is_symlink() or not source.resolve().is_relative_to(root):
            raise ValueError('Une source sort du dépôt ou est un lien symbolique.')
        if not source.is_file():
            continue
        target = destination / name
        if not target.resolve().is_relative_to(destination):
            raise ValueError('Une destination sort de la sauvegarde.')
        fingerprint = sha256(source)
        if target.exists() and (not target.is_file() or sha256(target) != fingerprint):
            raise ValueError(f'Une sauvegarde différente existe déjà : {name}')
        if apply and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256(target) != fingerprint:
                raise ValueError(f'Copie non conforme : {name}')
        rows.append({'source': name, 'bytes': source.stat().st_size, 'sha256': fingerprint})
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = destination / f'manifest-{stamp}.json'
        receipt.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=ROOT / '.local/media-archive')
    parser.add_argument('--apply', action='store_true', help='Copier les fichiers ; sans cette option, examiner seulement.')
    args = parser.parse_args()
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    rows = archive_files(ROOT, names, args.destination, apply=args.apply)
    print(f'{len(rows)} fichiers, {sum(row["bytes"] for row in rows)} octets ; ' + ('copie vérifiée' if args.apply else 'examen sans copie'))


if __name__ == '__main__':
    main()
