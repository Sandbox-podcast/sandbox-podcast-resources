"""Non-destructive thumbnail export and technical QA. Requires Pillow."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw


def prepare(paths, destination):
    if len(paths) != 3:
        raise ValueError('Exactly three images are required.')
    source_hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    if len(set(source_hashes)) != 3:
        raise ValueError('The three source files must differ.')
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Use a new or empty export directory; existing exports are preserved.')
    inputs = []
    for path in paths:
        with Image.open(path) as opened:
            opened.load()
            if abs(opened.width / opened.height - 16 / 9) > 0.015:
                raise ValueError(f'{path.name}: expected 16:9; recompose instead of cropping automatically.')
            if 'A' in opened.getbands() and opened.getchannel('A').getextrema()[0] < 250:
                raise ValueError(f'{path.name}: unfinished transparent thumbnail; composite before exporting.')
            inputs.append(opened.convert('RGB'))
    pixel_hashes = [hashlib.sha256(im.resize((320, 180)).tobytes()).hexdigest() for im in inputs]
    if len(set(pixel_hashes)) != 3:
        raise ValueError('The three images have identical rendered pixels.')
    destination.mkdir(parents=True, exist_ok=True)
    checks = []
    board = Image.new('RGB', (1008, 218), '#11151d')
    draw = ImageDraw.Draw(board)
    for index, (path, original) in enumerate(zip(paths, inputs)):
        name = 'ABC'[index]
        final = original.resize((1280, 720), Image.Resampling.LANCZOS)
        encoded, quality = None, None
        for candidate in (95, 90, 85, 80, 75):
            buffer = BytesIO()
            final.save(buffer, format='JPEG', quality=candidate, optimize=True, subsampling=0)
            if buffer.tell() < 2_000_000:
                encoded, quality = buffer.getvalue(), candidate
                break
        if encoded is None:
            raise ValueError(f'{name}: could not encode below 2 MB.')
        target = destination / f'{name}.jpg'
        target.write_bytes(encoded)
        preview = final.resize((320, 180), Image.Resampling.LANCZOS)
        preview.save(destination / f'{name}-320.jpg', quality=92)
        final.resize((160, 90), Image.Resampling.LANCZOS).save(destination / f'{name}-160.jpg', quality=92)
        board.paste(preview, (index * 336 + 8, 8))
        draw.text((index * 336 + 8, 194), name, fill='white')
        checks.append({'variant': name, 'source': str(path.resolve()), 'source_size': list(original.size), 'source_sha256': source_hashes[index], 'output': str(target), 'output_size': [1280, 720], 'bytes': len(encoded), 'jpeg_quality': quality, 'upscaled': original.width < 1280 or original.height < 720, 'visual_review': 'not_performed_by_this_script'})
    board.save(destination / 'comparison.jpg', quality=92)
    (destination / 'technical-checks.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', nargs=3, type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.images, args.out)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
