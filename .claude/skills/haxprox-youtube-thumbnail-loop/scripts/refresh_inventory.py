"""Refresh portable file hashes after an authorized skill update."""
import argparse
import hashlib
import json

from validate_package import ROOT, TEXT_EXTENSIONS


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--normalize-text', action='store_true', help='Use LF line endings for portable Git hashes.')
    parser.add_argument('--date', help='Optional explicit date for this package revision.')
    args = parser.parse_args()
    files = []
    for path in sorted(ROOT.rglob('*')):
        if path.is_symlink():
            parser.error('Symlinks are not portable: '+path.relative_to(ROOT).as_posix())
        if not path.is_file() or '__pycache__' in path.parts or path.suffix in {'.pyc', '.zip'}:
            continue
        if path == ROOT / 'assets/inventory.json':
            continue
        if args.normalize_text and path.suffix in TEXT_EXTENSIONS:
            text = path.read_text(encoding='utf-8-sig')
            path.write_text(text, encoding='utf-8', newline='\n')
        files.append({'path':path.relative_to(ROOT).as_posix(), 'bytes':path.stat().st_size,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    inventory = {'schema':1, 'path_base':'skill root', 'files':files}
    if args.date:
        inventory['date'] = args.date
    target = ROOT / 'assets/inventory.json'
    target.write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Inventory refreshed:', len(files), 'files')
