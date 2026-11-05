"""Inventory public /videos tabs, cache thumbnails and make numbered contact sheets.
Requires: pip install yt-dlp Pillow requests. No video or audio download.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from yt_dlp import YoutubeDL


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def download(entry, root):
    path = root / entry['image']
    if path.exists():
        try:
            with Image.open(path) as im:
                im.verify()
            entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            entry['downloaded_url'] = None
            return entry, None
        except Exception:
            pass
    errors = []
    urls = [entry['thumbnail_url'], f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg"]
    for url in dict.fromkeys(urls):
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=25)
                response.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                temp = path.with_suffix('.part')
                temp.write_bytes(response.content)
                with Image.open(temp) as im:
                    im.verify()
                temp.replace(path)
                entry['downloaded_url'] = url
                entry['sha256'] = hashlib.sha256(response.content).hexdigest()
                return entry, None
            except Exception as exc:
                errors.append(str(exc))
                time.sleep(0.3 * (attempt + 1))
    return entry, '; '.join(errors)


def boards(entries, root, slug, per_page=40):
    output = []
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 16)
    except OSError:
        font = ImageFont.load_default()
    columns, cell_w, cell_h = 5, 320, 209
    for offset in range(0, len(entries), per_page):
        batch = entries[offset:offset + per_page]
        canvas = Image.new('RGB', (columns * cell_w, 45 + ((len(batch) + columns - 1) // columns) * cell_h), '#10131a')
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 10), f'{slug} | {offset + 1}-{offset + len(batch)} | public /videos', font=font, fill='white')
        ids = []
        for n, entry in enumerate(batch):
            x, y = (n % columns) * cell_w, 45 + (n // columns) * cell_h
            path = root / entry['image']
            if path.exists():
                with Image.open(path) as im:
                    # hqdefault includes letterbox bars; crop exactly to 16:9 for boards only.
                    tile = ImageOps.fit(im.convert('RGB'), (312, 176))
                    canvas.paste(tile, (x + 4, y))
            draw.text((x + 4, y + 178), f"{entry['index']:04d} {entry['id']}", font=font, fill='white')
            ids.append(entry['id'])
        relative = f'boards/{slug}-{offset // per_page + 1:03d}.jpg'
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, quality=89)
        output.append({'path': relative, 'ids': ids, 'visually_reviewed': False})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--channel', action='append', help='Optional channel slug filter')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    config = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    summary = json.loads((root / 'coverage.json').read_text(encoding='utf-8')) if (root / 'coverage.json').exists() else []
    for channel in config['channels']:
        slug = channel['slug']
        if args.channel and slug not in args.channel:
            continue
        directory = root / slug
        directory.mkdir(parents=True, exist_ok=True)
        raw_path = directory / 'raw.json'
        try:
            if raw_path.exists() and not args.refresh:
                raw = json.loads(raw_path.read_text(encoding='utf-8'))
            else:
                with YoutubeDL({'extract_flat': True, 'skip_download': True, 'quiet': True, 'ignoreerrors': False, 'extractor_retries': 2, 'socket_timeout': 30}) as ydl:
                    raw = ydl.extract_info(channel['url'], download=False)
                write_json(raw_path, raw)
            entries, seen = [], set()
            for item in raw.get('entries', []):
                if not item or not item.get('id') or item['id'] in seen:
                    continue
                seen.add(item['id'])
                thumbs = item.get('thumbnails') or []
                thumbnail = max(thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0))['url'] if thumbs else f"https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg"
                entries.append({'index': len(entries) + 1, 'id': item['id'], 'title': item.get('title'), 'url': f"https://www.youtube.com/watch?v={item['id']}", 'thumbnail_url': thumbnail, 'view_count': item.get('view_count'), 'duration': item.get('duration'), 'image': f"images/{item['id']}.jpg", 'visual_annotation': None})
            failures = []
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(download, entry, directory) for entry in entries]
                for future in as_completed(futures):
                    entry, error = future.result()
                    if error:
                        failures.append({'id': entry['id'], 'error': error})
            sheets = boards(entries, directory, slug)
            manifest = {'channel': channel, 'channel_id': raw.get('channel_id'), 'channel_name': raw.get('channel'), 'enumerated_at': datetime.fromtimestamp(raw_path.stat().st_mtime, timezone.utc).isoformat(), 'prepared_at': datetime.now(timezone.utc).isoformat(), 'scope': 'public /videos tab only; no Shorts/live tabs, deleted/private videos or historic thumbnail variants', 'enumeration_status': 'extractor_returned_without_error', 'entries': entries, 'download_failures': failures, 'boards': sheets}
            write_json(directory / 'manifest.json', manifest)
            result = {'slug': slug, 'enumerated': len(entries), 'downloaded': len(entries) - len(failures), 'boards': len(sheets), 'status': manifest['enumeration_status']}
        except Exception as exc:
            result = {'slug': slug, 'status': 'error', 'error': str(exc)}
        summary = [row for row in summary if row['slug'] != slug] + [result]
        write_json(root / 'coverage.json', summary)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    atlas(root)


def atlas(root):
    """Offline index. Escape titles: remote metadata is untrusted display text."""
    cards, options, total = [], [], 0
    for manifest_path in sorted(root.glob('*/manifest.json')):
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        slug = data['channel']['slug']
        options.append(f'<option>{html.escape(slug)}</option>')
        for entry in data['entries']:
            total += 1
            title = entry.get('title') or entry['id']
            safe_title = html.escape(title)
            relative = f"{slug}/{entry['image']}"
            cards.append(f'<article data-channel="{slug}" data-search="{html.escape((slug + " " + title + " " + entry["id"]).lower(), quote=True)}"><a href="{relative}" target="_blank"><img loading="lazy" src="{relative}" alt="{safe_title}"></a><p>{slug} / {entry["index"]:04d}</p><a href="{html.escape(entry["url"], quote=True)}" target="_blank" rel="noreferrer">{safe_title}</a><small>{entry["id"]}</small></article>')
    page = '''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Corpus des miniatures de Lou</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{background:#11151d;color:#f2f4f8;font:16px Arial;margin:24px}header{position:sticky;top:0;background:#11151def;padding:12px 0;z-index:1}h1{font-size:28px}input,select{padding:12px;font:inherit;margin:4px;background:#202938;color:white;border:1px solid #73839c;border-radius:6px}input{width:min(460px,75vw)}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:22px}article{background:#202938;padding:8px;border-radius:8px}img{width:100%;aspect-ratio:16/9;object-fit:cover}a{color:#a4d5ff;text-decoration:none}a:hover{text-decoration:underline}p,small{color:#c0c9d8}small{display:block;margin-top:8px}article[hidden]{display:none}</style><header><h1>Corpus des miniatures de Lou</h1><p>COUNT images publiques des onglets Vidéos. Cliquer sur une image pour l'ouvrir, sur le titre pour ouvrir la vidéo.</p><label>Chaîne <select id="channel"><option value="">Toutes</option>OPTIONS</select></label><label>Recherche <input id="search" type="search" placeholder="Sujet, outil, identifiant"></label><p id="count" aria-live="polite"></p></header><main>CARDS</main><script>const cards=[...document.querySelectorAll('article')],s=document.querySelector('#search'),c=document.querySelector('#channel');function filter(){let n=0;for(const el of cards){el.hidden=!!((c.value&&el.dataset.channel!==c.value)||!el.dataset.search.includes(s.value.toLowerCase()));if(!el.hidden)n++}document.querySelector('#count').textContent=n+' miniatures affichées'}s.addEventListener('input',filter);c.addEventListener('change',filter);filter();</script></html>'''
    page = page.replace('COUNT', str(total)).replace('OPTIONS', ''.join(options)).replace('CARDS', ''.join(cards))
    (root / 'atlas.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    main()
