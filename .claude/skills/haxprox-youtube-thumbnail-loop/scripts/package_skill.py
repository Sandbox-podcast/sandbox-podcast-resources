"""Validate and ZIP this skill without following external paths or bundling caches."""
import argparse
from pathlib import Path
import zipfile

from validate_package import ROOT, validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    target = args.out.resolve()
    if target.is_relative_to(ROOT):
        parser.error('Write the archive outside the skill folder to avoid self-inclusion.')
    result = validate(check_hashes=True)
    if result['status'] != 'pass':
        parser.error(str(result['errors']))
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(ROOT.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc','.zip'}:
                archive.write(path, ROOT.name+'/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive integrity failure')
    print('Archive created:', target.name, '| bytes:', target.stat().st_size)
