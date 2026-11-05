"""Check the bundled files and relative links, independently of the current directory."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEXT_EXTENSIONS = {'.md', '.json', '.py', '.txt', '.csv', '.html', '.yaml', '.yml'}
HOST_PATH = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]:[/\\]|file:[/]{2}|/(?:Users|home|mnt|workspace)/')


def local_file(value):
    target = (ROOT / value).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError('Resource escapes package: '+value)
    if not target.exists():
        raise ValueError('Missing resource: '+value)
    return target


def check_root_paths(data, errors):
    if isinstance(data, dict):
        for item in data.values():
            check_root_paths(item, errors)
    elif isinstance(data, list):
        for item in data:
            check_root_paths(item, errors)
    elif isinstance(data, str) and data.startswith('assets/') and '\n' not in data:
        try:
            local_file(data)
        except ValueError as error:
            errors.append(str(error))


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attributes):
        self.links.extend(v for k, v in attributes if k in {'src', 'href'} and v)


def validate(check_hashes=False):
    errors = []
    inventory_path = ROOT / 'assets/inventory.json'
    if not inventory_path.is_file():
        raise ValueError('Missing assets/inventory.json')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    for item in inventory['files']:
        try:
            path = local_file(item['path'])
            if path.stat().st_size != item['bytes']:
                errors.append('Size mismatch: '+item['path'])
            if check_hashes and hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                errors.append('Hash mismatch: '+item['path'])
        except ValueError as error:
            errors.append(str(error))

    for path in ROOT.rglob('*'):
        if path.is_symlink():
            errors.append('Symlink is not portable: '+path.relative_to(ROOT).as_posix())
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        relative = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding='utf-8-sig')
        if HOST_PATH.search(content):
            errors.append('Machine-specific path: '+relative)
        if path.suffix == '.json':
            try:
                check_root_paths(json.loads(content), errors)
            except json.JSONDecodeError as error:
                errors.append(relative+': '+str(error))
        links = []
        if path.suffix == '.md':
            links = re.findall(r'!?\[[^\]]*\]\(([^)\n]+)\)', content)
        elif path.suffix == '.html':
            parser = LocalLinks()
            parser.feed(content)
            links = parser.links
        for link in links:
            url = urlsplit(link.strip('<>'))
            if url.scheme or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append('Broken local link in '+relative+': '+link)

    bank = ROOT / 'assets/identity/lou/portraits'
    manifest = json.loads((bank / 'manifest.json').read_text(encoding='utf-8'))
    if len(manifest['assets']) != 40:
        errors.append('Expected 40 portrait entries')
    for item in manifest['assets']:
        path = bank / 'png' / item['file']
        with Image.open(path) as image:
            if list(image.size) != item['dimensions'] or 'A' not in image.getbands():
                errors.append('Portrait dimensions/alpha mismatch: '+item['file'])
        if check_hashes and hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            errors.append('Portrait source hash mismatch: '+item['file'])

    corpus = ROOT / 'assets/corpus/2026-11-01'
    coverage = json.loads((corpus / 'coverage.json').read_text(encoding='utf-8'))
    count = 0
    if len(coverage) != 7:
        errors.append('Expected seven channels')
    for channel in coverage:
        data = json.loads((corpus / channel['slug'] / 'manifest.json').read_text(encoding='utf-8'))
        for entry in data['entries']:
            path = corpus / channel['slug'] / entry['image']
            if not path.is_file():
                errors.append('Missing corpus image: '+entry['id'])
            elif check_hashes and hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                errors.append('Corpus source hash mismatch: '+entry['id'])
            count += 1
    if count != 1128:
        errors.append('Expected 1128 frozen corpus thumbnails')

    example = ROOT / 'assets/examples/sandbox-equipe-tech-ia/exports'
    for letter in 'ABC':
        path = example / (letter+'.jpg')
        with Image.open(path) as image:
            if image.size != (1280, 720) or path.stat().st_size >= 2000000:
                errors.append('Invalid approved export: '+letter)
        for suffix, expected in [('-320', (320, 180)), ('-160', (160, 90))]:
            with Image.open(example / (letter+suffix+'.jpg')) as image:
                if image.size != expected:
                    errors.append('Invalid approved preview: '+letter+suffix)

    return {'status':'pass' if not errors else 'fail', 'inventory_files':len(inventory['files']),
            'portraits':len(manifest['assets']), 'channels':len(coverage), 'corpus_images':count,
            'hashes_checked':check_hashes, 'errors':sorted(set(errors))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hashes', action='store_true')
    options = parser.parse_args()
    try:
        result = validate(options.hashes)
    except (ValueError, OSError, KeyError) as error:
        result = {'status':'fail', 'errors':[str(error)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'pass' else 1)
