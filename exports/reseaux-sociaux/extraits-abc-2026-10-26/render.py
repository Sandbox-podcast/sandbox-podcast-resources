"""Composition native des variantes B/C avec les portraits existants de Sandbox."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HOME = ROOT / 'apps/site/public/images/home'
FONT = 'C:/Windows/Fonts/arialbd.ttf'
VIDEOS = [
    ('RijXj9iSR94', 'Sillage', 'episode-01/video-02-7720e7711605', 'nicolas', ['TES AGENTS', 'DANS LA', 'POCHE'], ['CODER DEPUIS', 'SON TÉLÉPHONE'], 'SILLAGE'),
    ('OQxyNKJblfI', 'Harnais', 'episode-01/video-01-67950a8a1d3e', 'loic', ['LE MODÈLE', 'SUFFIT-IL ?'], ['CODEX', 'CLAUDE CODE', 'OPENCODE'], 'LE HARNAIS COMPTE'),
    ('dDKvDcYLaz4', 'Legacy', 'episode-02/video-02-7482544ad36a', 'nicolas', ['TOUT', 'RÉÉCRIRE', 'AVEC L’IA ?'], ['GARDER OU', 'RÉÉCRIRE ?'], 'CODE LEGACY'),
    ('QbhrC25L3sU', 'Artisans', 'episode-02/video-03-6401ee727e55', 'lou', ['L’IA DANS', 'TON MÉTIER'], ['DEVIS', 'COMMANDES', 'CLIENTS'], 'ARTISANS & COMMERÇANTS'),
    ('MT1VIi7P3P4', 'Tickets', 'episode-02/video-01-e1b008490b87', 'lou', ['TU LIS', 'ENCORE', 'LES TICKETS ?'], ['UN TICKET', 'SUFFIT À L’IA ?'], 'CODER AVEC L’IA'),
]

def font(size):
    return ImageFont.truetype(FONT, size)

def portrait(canvas, who, x, y, height):
    photo = Image.open(HOME / f'{who}-body-no-mic-v2.webp').convert('RGBA')
    photo = photo.crop(photo.getbbox())
    photo = photo.resize((round(photo.width * height / photo.height), height), Image.Resampling.LANCZOS)
    canvas.paste(photo, (x, y), photo)

def lines(draw, words, x, y, width, size, ink, accent):
    while max(draw.textbbox((0, 0), word, font=font(size))[2] for word in words) > width:
        size -= 1
    for i, word in enumerate(words):
        draw.text((x, y+i*(size+10)), word, font=font(size), fill=accent if i == len(words)-1 else ink, stroke_width=0)

manifest = []
for vid, subject, source, who, b, c, label in VIDEOS:
    directory = OUT / vid
    directory.mkdir(parents=True, exist_ok=True)
    control = ROOT / '.local/youtube-thematic' / source / 'thumbnail.png'
    Image.open(control).convert('RGB').save(directory / 'A.jpg', quality=95)
    for variant, words in [('B', b), ('C', c)]:
        light = variant == 'C'
        bg, ink, accent = ('#f7ecd7', '#071322', '#006b77') if light else ('#071322', '#ffffff', '#42e8de')
        image = Image.new('RGB', (1280,720), bg)
        draw = ImageDraw.Draw(image)
        if light:
            draw.polygon([(800,0),(1280,0),(1280,720),(680,720)], fill='#124252')
            draw.ellipse((830,100,1390,660), fill='#1f6574')
        else:
            draw.ellipse((720,-50,1420,850), fill='#123646')
            draw.line([(780,0),(680,720)], fill='#42e8de', width=9)
        portrait(image, who, 635 if who == 'lou' else 735, 75, 750)
        draw = ImageDraw.Draw(image)
        draw.text((54,38), 'SANDBOX', fill=accent, font=font(30))
        draw.text((54,100), label, fill=ink, font=font(23))
        lines(draw, words, 50, 210 if len(words)>2 else 250, 690, 112, ink, accent)
        draw.rectangle((54,655,170,663), fill=accent)
        image.save(directory / f'{variant}.jpg', quality=95, subsampling=0)
    manifest.append({'video_id': vid, 'subject': subject, 'A': 'miniature actuelle, témoin', 'B': ' / '.join(b), 'C': ' / '.join(c), 'status': 'prepared'})

(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
sheet = Image.new('RGB', (960, 5*206), '#151c25')
for row, (vid, *_rest) in enumerate(VIDEOS):
    for col, variant in enumerate('ABC'):
        thumb = Image.open(OUT / vid / f'{variant}.jpg')
        thumb.thumbnail((312,176))
        sheet.paste(thumb, (col*320, row*206+26))
        ImageDraw.Draw(sheet).text((col*320+8,row*206+3), f'{vid} / {variant}', font=font(16), fill='white')
sheet.save(OUT / 'contact-sheet.jpg', quality=95)
print(OUT)
