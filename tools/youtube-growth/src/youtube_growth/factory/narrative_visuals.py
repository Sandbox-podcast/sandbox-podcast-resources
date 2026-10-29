"""Sandbox's reusable animated diagrams, with separate portrait compositions."""
from __future__ import annotations

import math
from pathlib import Path
import shutil
import subprocess

from .contracts import ROOT, digest
from .media import _scan, _srt_time, fingerprint, probe, _load_stage, _save_stage, _frames

PALETTE = {"background": "#071322", "panel": "#10243B", "cyan": "#16D5E8", "white": "#F1F6FC", "muted": "#A6B9CC", "orange": "#FFB463"}
STYLE_VERSION = 2


def font_file():
    for path in (ROOT / "projects/videos/la-beta-jingle/assets/LeagueGothic-Condensed.ttf",
                 Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if path.exists():
            return path
    raise ValueError("Police locale requise pour les schémas narratifs.")


def wrap(draw, value, font, width):
    lines, line = [], ""
    for word in value.split():
        test = (line+" "+word).strip()
        if draw.textlength(test, font=font) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def frame(scene, speech, second, size, *, font_path=None, logo=None):
    from PIL import Image, ImageDraw, ImageFont
    width, height = size
    portrait = height > width
    scale = width / (540 if portrait else 960)
    im = Image.new("RGB", size, PALETTE["background"])
    draw = ImageDraw.Draw(im)
    font_path = font_path or font_file()
    fonts = {k: ImageFont.truetype(str(font_path), max(10, round(n*scale))) for k, n in
             (("brand", 16), ("heading", 33 if portrait else 35), ("node", 22), ("caption", 20), ("tag", 13))}
    margin = round(38*scale)
    duration = speech["duration_seconds"]
    progress = min(1, second / duration)
    # Every scene has finite, seekable node reveals and a signal travelling along its explanation.
    entrance = 1-(1-min(1, second/.55))**3
    dx = round((1-entrance)*width*.12)
    draw.rectangle((0, 0, width, round(6*scale)), fill=PALETTE["cyan"])
    roles = {"hook": "L'EXPÉRIENCE", "context": "LE PARCOURS", "stakes": "LE PROBLÈME", "development": "L'EXPLICATION", "conclusion": "LES CONSÉQUENCES"}
    draw.text((margin, round(29*scale)), "SANDBOX / " + roles.get(scene["role"], "LE SUJET"), font=fonts["brand"], fill=PALETTE["cyan"])
    if logo is not None:
        badge = logo.copy()
        badge.thumbnail((round(100*scale), round(38*scale)))
        im.paste(badge, (width-margin-badge.width, round(25*scale)), badge)
    y = round(82*scale)
    for line in wrap(draw, scene["heading"], fonts["heading"], width-margin*2):
        draw.text((margin+dx, y), line, font=fonts["heading"], fill=PALETTE["white"])
        y += round(43*scale)
    kind = scene["visual"]["type"]
    labels = scene["visual"]["labels"]
    top = max(round(210*scale), y+round(28*scale))
    bottom = height-round((250 if portrait else 152)*scale)
    nodes = []
    for index, label in enumerate(labels):
        if portrait or kind == "timeline":
            card_h = min(round(95*scale), (bottom-top-round(18*scale)*(len(labels)-1))//len(labels))
            x1, y1 = margin, top+index*(card_h+round(18*scale))
            x2, y2 = width-margin, y1+card_h
        elif kind in {"comparison", "cards"}:
            cols = 2
            card_w = (width-margin*2-round(22*scale))//2
            card_h = (bottom-top-round(18*scale))//(math.ceil(len(labels)/cols))
            x1, y1 = margin+(index%cols)*(card_w+round(22*scale)), top+(index//cols)*(card_h+round(18*scale))
            x2, y2 = x1+card_w, y1+card_h
        else:
            gap = round(32*scale)
            card_w = (width-margin*2-gap*(len(labels)-1))//len(labels)
            x1, y1 = margin+index*(card_w+gap), top+round(25*scale)
            x2, y2 = x1+card_w, min(bottom, y1+round(130*scale))
        reveal = min(1, max(0, (second-index*.22)/.42))
        if reveal <= 0:
            continue
        offset = round((1-reveal)*25*scale)
        y1, y2 = y1+offset, y2+offset
        active = min(len(labels)-1, int(progress*len(labels))) == index
        color = PALETTE["cyan"] if active else PALETTE["muted"]
        draw.rounded_rectangle((x1, y1, x2, y2), radius=round(13*scale), fill=PALETTE["panel"], outline=color, width=max(1, round((3 if active else 1)*scale)))
        lines = wrap(draw, label, fonts["node"], x2-x1-round(24*scale))
        line_h = round(28*scale)
        if len(lines)*line_h > y2-y1-round(10*scale):
            raise ValueError("Libellé trop long pour sa composition ; réviser le storyboard.")
        for j, line in enumerate(lines):
            tx = (x1+x2-draw.textlength(line, font=fonts["node"]))/2
            draw.text((tx, (y1+y2-len(lines)*line_h)/2+j*line_h), line, font=fonts["node"], fill=PALETTE["white"])
        nodes.append((x1, y1, x2, y2))
    if kind in {"flow", "timeline"}:
        for a, b in zip(nodes, nodes[1:]):
            p = ((a[0]+a[2])/2, a[3]) if portrait or kind == "timeline" else (a[2], (a[1]+a[3])/2)
            q = ((b[0]+b[2])/2, b[1]) if portrait or kind == "timeline" else (b[0], (b[1]+b[3])/2)
            draw.line((*p, *q), fill=PALETTE["cyan"], width=max(1, round(2*scale)))
            phase = (second*.65) % 1
            x, y = p[0]+(q[0]-p[0])*phase, p[1]+(q[1]-p[1])*phase
            r = 4*scale
            draw.ellipse((x-r, y-r, x+r, y+r), fill=PALETTE["orange"])
    tag_y = height-round((221 if portrait else 123)*scale)
    tags = {"fact": "FAIT SOURCÉ", "analysis": "ANALYSE SANDBOX", "hypothesis": "HYPOTHÈSE", "testimony": "TÉMOIGNAGE DANS L'ÉMISSION"}
    draw.text((margin, tag_y), tags[scene["statement_kind"]], font=fonts["tag"], fill=PALETTE["orange"])
    caption = next((s["caption"] for s in speech["sentences"] if s["start_seconds"] <= second < s["end_seconds"]), "")
    caption_lines = wrap(draw, caption, fonts["caption"], width-margin*2)
    if len(caption_lines) > (6 if portrait else 3):
        raise ValueError("Sous-titre de phrase trop long ; ponctuer ou découper la narration.")
    cy = tag_y+round(25*scale)
    for line in caption_lines:
        draw.text((margin, cy), line, font=fonts["caption"], fill=PALETTE["white"])
        cy += round(26*scale)
    draw.rectangle((margin, height-round(22*scale), margin+(width-margin*2)*progress, height-round(18*scale)), fill=PALETTE["cyan"])
    return im


def render(board, audio, directory, config, *, draft=False):
    from PIL import Image
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg requis.")
    portrait = board["format"] == "vertical"
    size = ((540, 960) if portrait else (960, 540)) if draft else ((1080, 1920) if portrait else (1280, 720))
    fps = 12 if draft else 24
    font = font_file()
    brand_path = ROOT / "assets/brand/logo.png"
    with Image.open(brand_path) as source:
        logo = source.convert("RGBA")
    directory.mkdir(parents=True, exist_ok=True)
    identity = {"style": STYLE_VERSION, "board": board, "audio": audio, "size": size, "fps": fps,
                "font_sha256": fingerprint(font), "logo_sha256": fingerprint(brand_path)}
    segments, artifacts, previews = [], [], []
    for scene, speech in zip(board["scenes"], audio["scenes"]):
        scene_identity = {"version": STYLE_VERSION, "scene": scene, "speech": speech, "size": size, "fps": fps,
                          "font": identity["font_sha256"], "logo": identity["logo_sha256"]}
        name = scene["beat_id"]+"-"+digest(scene_identity)[:12]
        path, receipt = directory/(name+".mp4"), directory/(name+".json")
        previous = _load_stage(receipt, scene_identity)
        if previous:
            partial = directory/(name+".partial.mp4")
            if not path.exists() and partial.exists() and fingerprint(partial) == previous["sha256"]:
                partial.replace(path)
            if fingerprint(path) != previous["sha256"]:
                raise ValueError("Scène terminée modifiée.")
        else:
            if path.exists():
                raise ValueError("Scène sans reçu ; aucun écrasement automatique.")
            partial = directory/(name+".partial.mp4")
            log_path = directory/(name+".ffmpeg.log")
            command = [ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "pipe:0", "-i", speech["path"],
                       "-map", "0:v:0", "-map", "1:a:0", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-t", str(speech["duration_seconds"]), "-movflags", "+faststart", str(partial)]
            with log_path.open("wb") as log:
                child = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log, stdout=subprocess.DEVNULL)
                try:
                    for index in range(math.ceil(speech["duration_seconds"]*fps)):
                        child.stdin.write(frame(scene, speech, index/fps, size, font_path=font, logo=logo).tobytes())
                    child.stdin.close()
                    if child.wait(timeout=120):
                        raise RuntimeError("Échec du rendu de scène ; consulter le journal local.")
                finally:
                    if child.stdin and not child.stdin.closed:
                        child.stdin.close()
                    if child.poll() is None:
                        child.terminate()
                        child.wait(timeout=10)
            _save_stage(receipt, scene_identity, {"sha256": fingerprint(partial)})
            partial.replace(path)
        preview = directory/(name+".png")
        if not preview.exists():
            frame(scene, speech, min(3, speech["duration_seconds"]/2), size, font_path=font, logo=logo).save(preview)
        previews.append(str(preview))
        segments.append(path)
        artifacts.extend({"path": str(p), "sha256": fingerprint(p)} for p in (path, preview))
    final = directory/"video.mp4"
    final_receipt = directory/"video-stage.json"
    final_identity = {"identity": identity, "segments": [fingerprint(s) for s in segments]}
    previous = _load_stage(final_receipt, final_identity)
    if previous:
        partial = directory/"video.partial.mp4"
        if not final.exists() and partial.exists() and fingerprint(partial) == previous["sha256"]:
            partial.replace(final)
        if fingerprint(final) != previous["sha256"]:
            raise ValueError("Vidéo narrative modifiée.")
    else:
        if final.exists():
            raise ValueError("Vidéo sans reçu ; aucun écrasement automatique.")
        playlist = directory/"concat.txt"
        if any("'" in str(p) or "\n" in str(p) for p in segments):
            raise ValueError("Chemin de scène incompatible avec concat.")
        playlist.write_text("\n".join("file '"+p.as_posix()+"'" for p in segments), encoding="utf-8")
        partial = directory/"video.partial.mp4"
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(playlist),
                        "-c", "copy", "-movflags", "+faststart", str(partial)], check=True, capture_output=True)
        _save_stage(final_receipt, final_identity, {"sha256": fingerprint(partial)})
        partial.replace(final)
    technical, actual = _scan(final), probe(final)
    video = next(s for s in actual["streams"] if s["codec_type"] == "video")
    if abs(actual["duration_seconds"]-audio["duration_seconds"]) > len(segments)/fps+.2 or (video["width"], video["height"]) != size:
        raise ValueError("Durée ou ratio du rendu narratif incorrect.")
    captions, count = [], 0
    for scene in audio["scenes"]:
        for sentence in scene["sentences"]:
            count += 1
            a, b = scene["start_seconds"]+sentence["start_seconds"], scene["start_seconds"]+sentence["end_seconds"]
            captions.append(f"{count}\n{_srt_time(a)} --> {_srt_time(b)}\n{sentence['caption']}\n")
    subtitle = directory/"subtitles.srt"
    subtitle.write_text("\n".join(captions), encoding="utf-8-sig")
    artifacts.extend({"path": str(p), "sha256": fingerprint(p)} for p in (final, subtitle))
    return {"path": str(final), "sha256": fingerprint(final), "subtitle_path": str(subtitle), "width": size[0], "height": size[1],
            "duration_seconds": actual["duration_seconds"], "fps": fps, "format": board["format"], "previews": previews,
            "artifacts": artifacts, "qa": {"technical": technical, "visual": "pending", "audio": "pending",
                                          "editorial": "pending", "subtitles": "pending"},
            "quality": "draft" if draft else "delivery", "publication": "not_uploaded"}
