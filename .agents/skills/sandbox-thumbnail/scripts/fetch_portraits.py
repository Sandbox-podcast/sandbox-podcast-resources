"""Fetch the pinned Sandbox portraits into an explicit local directory."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(output):
    manifest = Path(__file__).resolve().parents[1] / 'references' / 'portraits.json'
    portraits = json.loads(manifest.read_text(encoding='utf-8'))['portraits']
    output.mkdir(parents=True, exist_ok=True)
    for portrait in portraits:
        filename = portrait['filename']
        if Path(filename).name != filename:
            raise ValueError('Nom de fichier invalide dans le manifeste.')
        target = output / filename
        expected = portrait['sha256']
        if target.exists():
            if digest(target.read_bytes()) != expected:
                raise ValueError(f'Fichier différent, conservé sans écrasement : {target}')
            print(f"{portrait['name']} : déjà vérifié ({target})")
            continue
        with urllib.request.urlopen(portrait['url'], timeout=30) as response:
            data = response.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024 or digest(data) != expected:
            raise ValueError(f"Téléchargement refusé : taille ou empreinte incorrecte ({filename}).")
        # Exclusive creation also prevents overwriting a file created during download.
        with target.open('xb') as stream:
            stream.write(data)
        print(f"{portrait['name']} : téléchargé et vérifié ({target})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Dossier local des portraits, hors Git')
    args = parser.parse_args()
    try:
        fetch(args.output.expanduser().resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f'Portraits : {error}\n')
