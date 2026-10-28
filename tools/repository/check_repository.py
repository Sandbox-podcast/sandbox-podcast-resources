"""Reject local production data in the Git index, even when added with -f."""
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SHARED_IMAGES = frozenset({'assets/brand/logo.png', 'docs/readme/hero.png'})
MEDIA_SUFFIXES = frozenset({
    '.mp4', '.mov', '.mkv', '.webm', '.avi', '.mp3', '.m4a', '.aac', '.wav',
    '.flac', '.ogg', '.opus', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif',
    '.zip', '.7z', '.tar', '.gz', '.srt', '.ass', '.vtt', '.sqlite', '.sqlite3', '.db',
})
LEGACY_ROOTS = frozenset({
    'Episode 2', 'SANDBOX_LinkedIn_Kit', 'SANDBOX_LinkedIn_Kit.zip', 'exports',
    'kits-relais', 'media', 'output', 'videos', 'experiments', 'brand', 'old',
    'logo rs', 'logo rs2',
})
LOCAL_PARTS = frozenset({'.local', '.state', 'renders', 'proof', 'analysis', 'output', 'outputs', 'dist'})


def local_only(name: str) -> bool:
    path = PurePosixPath(name.replace('\\', '/'))
    if path.as_posix() in SHARED_IMAGES:
        return False
    return bool(
        path.parts[0] in LEGACY_ROOTS
        or set(path.parts) & LOCAL_PARTS
        or path.suffix.lower() in MEDIA_SUFFIXES
        or (path.parts[:2] == ('projects', 'videos') and 'public' in path.parts)
        or (path.parts[:2] == ('projects', 'experiments') and 'assets' in path.parts)
        or (path.parts[:2] == ('projects', 'relay-kits') and set(path.parts) & {'assets', 'captions'})
    )


def main() -> int:
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    rejected = sorted(name for name in tracked if name and local_only(name))
    if rejected:
        print('Fichiers réservés au stockage local présents dans Git :')
        for name in rejected:
            print(f'  {name}')
        print('Conserver ces fichiers sur le poste, hors du suivi Git. Voir docs/organisation.md.')
        return 1
    print('Git contient uniquement les sources partagées et les illustrations autorisées.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
