from __future__ import annotations

import io
import re
import textwrap
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


NAVY = (7, 19, 34)
CYAN = (66, 232, 222)
WHITE = (249, 251, 255)


def safe_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", normalized).strip("-").lower()
    return slug[:64] or "episode"


def thumbnail_url(thumbnails: dict[str, dict[str, str]]) -> str | None:
    for size in ("maxres", "standard", "high", "medium", "default"):
        item = thumbnails.get(size)
        if isinstance(item, dict) and item.get("url"):
            return item["url"]
    return None


def _fetch_thumbnail(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not (parsed.hostname == "i.ytimg.com" or (parsed.hostname or "").endswith(".ytimg.com")):
        raise ValueError("La miniature source doit provenir d'un hôte HTTPS ytimg.com.")
    request = Request(url, headers={"User-Agent": "SANDBOX-YouTube-ops/1.0"})
    with urlopen(request, timeout=15) as response:
        content_type = response.headers.get_content_type()
        content = response.read(10_000_001)
    if content_type not in {"image/jpeg", "image/png", "image/webp"} or len(content) > 10_000_000:
        raise ValueError("Format ou taille de miniature source invalide.")
    return content


def _font(size: int, bold: bool = True):
    from PIL import ImageFont

    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_variants(source_bytes: bytes, title: str, output_dir: Path, video_id: str) -> list[Path]:
    """Rend trois concepts PNG; ils ne sont pas téléversés ni testés automatiquement sur YouTube."""
    try:
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
    except ImportError as error:
        raise RuntimeError("Installez Pillow avec requirements.txt pour générer les miniatures.") from error

    source = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    canvas = ImageOps.fit(source, (1280, 720), method=Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Brightness(canvas).enhance(0.60).filter(ImageFilter.GaussianBlur(1.2))
    wrapped = textwrap.wrap(title.strip() or "Nouvel épisode", width=27, break_long_words=True)[:3]
    if not wrapped:
        wrapped = ["Nouvel épisode"]
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []

    for variant in ("cyan-panel", "bold-title", "quote-card"):
        image = canvas.copy()
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        title_font = _font(68)
        label_font = _font(26)
        line_height = 84
        text_height = len(wrapped) * line_height
        if variant == "cyan-panel":
            draw.rectangle((0, 0, 470, 720), fill=(*NAVY, 220))
            draw.rectangle((0, 0, 18, 720), fill=(*CYAN, 255))
            draw.text((66, 92), "SANDBOX  ·  IA", font=label_font, fill=(*CYAN, 255))
            text_x, text_y = 66, max(210, (720 - text_height) // 2)
            text_fill = (*WHITE, 255)
        elif variant == "bold-title":
            draw.rectangle((0, 0, 1280, 175), fill=(*NAVY, 185))
            draw.rectangle((0, 160, 1280, 172), fill=(*CYAN, 255))
            draw.text((64, 46), "SANDBOX  ·  PODCAST IA", font=label_font, fill=(*CYAN, 255))
            text_x, text_y = 66, 228
            text_fill = (*WHITE, 255)
        else:
            draw.rounded_rectangle((54, 412, 1226, 672), radius=26, fill=(*NAVY, 236), outline=(*CYAN, 255), width=4)
            draw.text((92, 436), "À DÉCOUVRIR", font=label_font, fill=(*CYAN, 255))
            text_x, text_y = 92, 486
            text_fill = (*WHITE, 255)

        for index, line in enumerate(wrapped):
            draw.text((text_x, text_y + index * line_height), line, font=title_font, fill=text_fill, stroke_width=2, stroke_fill=(*NAVY, 230))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        path = output_dir / f"{video_id}-{variant}.png"
        image.save(path, format="PNG", optimize=True)
        results.append(path)
    return results


def fetch_and_render(url: str, title: str, output_dir: Path, video_id: str) -> list[Path]:
    return render_variants(_fetch_thumbnail(url), title, output_dir, video_id)
