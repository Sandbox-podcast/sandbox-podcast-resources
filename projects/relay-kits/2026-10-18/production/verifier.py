"""Vérifie les médias livrés, leurs empreintes et les liens Markdown locaux."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

KIT = Path(__file__).resolve().parents[4] / '.local/relay-kits/2026-10-18'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--decode',action='store_true',help='Décoder intégralement chaque vidéo distincte')
    args=parser.parse_args()
    manifest=json.loads((KIT/'assets.json').read_text(encoding='utf-8'))['assets']
    errors=[]
    decoded=set()
    for asset in manifest:
        path=(KIT/asset['file']).resolve()
        if not path.is_relative_to(KIT.resolve()) or not path.is_file():
            errors.append(f"Fichier absent ou hors du kit : {asset['file']}")
            continue
        with path.open('rb') as stream:
            actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=asset['sha256'] or path.stat().st_size!=asset['bytes']:
            errors.append(f"Empreinte ou taille différente : {asset['file']}")
        if path.stat().st_size >= 49*1024*1024:
            errors.append(f"Fichier supérieur au plafond de 49 Mio : {asset['file']}")
        if args.decode and path.suffix=='.mp4' and actual not in decoded:
            result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(path),'-f','null','-'],capture_output=True,text=True,encoding='utf-8',errors='replace')
            if result.returncode:
                errors.append(f"Décodage échoué : {asset['file']} : {result.stderr[-400:]}")
            decoded.add(actual)
    links=0
    for doc in KIT.rglob('*.md'):
        if '.hyperframes' in doc.parts or doc.name in {'AGENTS.md','CLAUDE.md'}:
            continue
        for href in re.findall(r'\]\(([^\s)]+)\)',doc.read_text(encoding='utf-8')):
            if href.startswith(('http:','https:','#','mailto:')):
                continue
            target=(doc.parent/unquote(href.split('#')[0])).resolve()
            if not target.exists():
                errors.append(f'Lien local absent dans {doc.relative_to(KIT)} : {href}')
            links+=1
    print(json.dumps({'assets':len(manifest),'localLinks':links,'distinctVideosDecoded':len(decoded),'errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors else 0)


if __name__=='__main__':
    main()
