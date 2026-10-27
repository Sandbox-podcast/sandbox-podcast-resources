"""FFmpeg horizontal exports, independent of Shorts and all upload code."""
from __future__ import annotations

import json
from pathlib import Path

from .shorts import _call, _sha256
from .storage import digest, save_json
from .thumbnails import CYAN, NAVY, WHITE, _font


def probe(path: Path, ffprobe: str) -> dict:
    return json.loads(_call([ffprobe, "-v", "error", "-show_entries",
                            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,start_time,duration,sample_aspect_ratio",
                            "-of", "json", str(path)]))


def canvas(info: dict) -> tuple[int, int, str]:
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not video or not any(s["codec_type"] == "audio" for s in info["streams"]):
        raise ValueError("La source doit contenir vidéo et audio.")
    ratio = video.get("sample_aspect_ratio", "1:1")
    if ratio not in {"1:1", "N/A"}:
        raise ValueError("Pixels non carrés : normalisez explicitement une copie de la source.")
    # Keep every source pixel without stretching/cropping; pad to exact 16:9, never upscale.
    factor = min(video["width"] // 32, video["height"] // 18)
    if factor < 1:
        raise ValueError("Résolution source insuffisante.")
    return factor * 32, factor * 18, video["r_frame_rate"]


def verify(path: Path, duration: float, size: tuple[int, int], ffmpeg: str, ffprobe: str) -> dict:
    info = probe(path, ffprobe)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    actual = float(info["format"]["duration"])
    if abs(actual - duration) > .25 or not 300 <= actual <= 900.25:
        raise RuntimeError("Durée du rendu non conforme (5 à 15 minutes).")
    if (video["width"], video["height"]) != size or video["codec_name"] != "h264" or audio["codec_name"] != "aac":
        raise RuntimeError("Format de rendu non conforme.")
    av_delta = abs(float(video.get("duration", actual)) - float(audio.get("duration", actual)))
    start_delta = abs(float(video.get("start_time", 0)) - float(audio.get("start_time", 0)))
    if av_delta > .15 or start_delta > .08:
        raise RuntimeError("Écart audio/vidéo au-delà de la tolérance.")
    _call([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    return {"status": "decoded", "duration": actual, "width": size[0], "height": size[1],
            "av_duration_delta": round(av_delta, 4), "av_start_delta": round(start_delta, 4), "sha256": _sha256(path)}


def render(source: Path, directory: Path, timeline: list[dict], info: dict, burn: bool, ffmpeg: str, ffprobe: str) -> dict:
    width, height, fps = canvas(info)
    from fractions import Fraction
    rate = float(Fraction(fps))
    parts = directory / "parts"
    parts.mkdir(exist_ok=True)
    # Quantize each part before calculating SRT/time mapping. Concat cannot accumulate
    # one fractional video frame of drift at every cut.
    cursor = 0.0
    for index, edit in enumerate(timeline):
        frames = round((edit["source_end"] - edit["source_start"]) * rate)
        duration = frames / rate
        edit.update(output_start=round(cursor, 6), output_end=round(cursor + duration, 6), frames=frames)
        cursor += duration
        part = parts / f"part-{index:03}.mp4"
        receipt = part.with_suffix(".json")
        expected = digest({"edit": edit, "width": width, "height": height, "fps": fps})
        if part.exists() and receipt.exists():
            previous = json.loads(receipt.read_text(encoding="utf-8"))
            if previous.get("edit") == expected and previous.get("sha256") == _sha256(part):
                continue
        temporary = part.with_suffix(".partial.mp4")
        _call([ffmpeg, "-nostdin", "-v", "error", "-y", "-ss", str(edit["source_start"]), "-i", str(source),
               "-t", f"{duration:.6f}", "-map", "0:v:0", "-map", "0:a:0",
               "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x071322,setsar=1",
               "-r", fps, "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
               "-af", f"aresample=48000,apad,atrim=duration={duration:.6f},afade=t=in:d=0.008,afade=t=out:st={max(0,duration-.008):.6f}:d=0.008",
               "-c:a", "aac", "-b:a", "192k", str(temporary)])
        temporary.replace(part)
        save_json(receipt, {"edit": expected, "sha256": _sha256(part)})
    # A concat filter trims decoded AAC priming/padding to the exact frame duration.
    # This prevents cumulative AV drift across many short parts.
    inputs, filters, labels = [], [], []
    for index, edit in enumerate(timeline):
        inputs += ["-i", str(parts / f"part-{index:03}.mp4")]
        duration = edit["output_end"] - edit["output_start"]
        filters += [f"[{index}:v]trim=duration={duration:.6f},setpts=PTS-STARTPTS[v{index}]",
                    f"[{index}:a]atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[a{index}]"]
        labels.append(f"[v{index}][a{index}]")
    filters += ["".join(labels) + f"concat=n={len(timeline)}:v=1:a=1[v][a]",
                "[a]dynaudnorm=f=500:g=7:p=0.9,loudnorm=I=-16:TP=-1.5:LRA=11[audio]"]
    from .shorts import _subtitle_filter_path
    if burn:
        filters.append(f"[v]subtitles=filename='{_subtitle_filter_path(directory / 'subtitles.srt')}'[video]")
    else:
        filters.append("[v]null[video]")
    filter_file = directory / "render.ffscript"
    filter_file.write_text(";\n".join(filters), encoding="utf-8")
    temporary = directory / "video.partial.mp4"
    subtitle_input = [] if burn else ["-i", str(directory / "subtitles.srt")]
    subtitle_map = [] if burn else ["-map", f"{len(timeline)}:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=fra"]
    _call([ffmpeg, "-nostdin", "-v", "error", "-y", *inputs, *subtitle_input,
           "-filter_complex", filter_file.read_text(encoding="utf-8"), "-map", "[video]", "-map", "[audio]", *subtitle_map,
           "-t", f"{cursor:.6f}", "-r", fps, "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", str(temporary)])
    result = verify(temporary, cursor, (width, height), ffmpeg, ffprobe)
    temporary.replace(directory / "video.mp4")
    return result


def thumbnail(source: Path, directory: Path, caption: str, time: float, ffmpeg: str) -> None:
    from PIL import Image, ImageDraw, ImageOps
    frame = directory / "thumbnail-source.jpg"
    _call([ffmpeg, "-nostdin", "-v", "error", "-y", "-ss", str(time), "-i", str(source), "-frames:v", "1", str(frame)])
    image = Image.new("RGB", (1280, 720), NAVY)
    # These talkshow layouts place their real camera column at the right. Keep that
    # entire column (including all three speakers) rather than a decorative slide.
    with Image.open(frame) as raw:
        raw = raw.convert("RGB")
        strip = raw.crop((round(raw.width*.73), 0, raw.width, raw.height))
        shot = ImageOps.contain(strip, (440, 660))
    image.paste(shot, (815+(440-shot.width)//2, (720-shot.height)//2))
    draw = ImageDraw.Draw(image)
    draw.text((56, 54), "SANDBOX", fill=CYAN, font=_font(34))
    draw.rectangle((56, 113, 750, 119), fill=CYAN)
    font = _font(92)
    while True:
        lines = [""]
        for word in caption.split():
            trial = (lines[-1] + " " + word).strip()
            if lines[-1] and draw.textbbox((0, 0), trial, font=font)[2] > 700:
                lines.append(word)
            else:
                lines[-1] = trial
        if len(lines) <= 4 and max(draw.textbbox((0, 0), line, font=font)[2] for line in lines) <= 700:
            break
        font = _font(font.size-2)
    line_height = font.size+18
    top = 180+(450-line_height*len(lines))//2
    for index, line in enumerate(lines):
        draw.text((56, top+index*line_height), line, fill=CYAN if index == len(lines)-1 else WHITE, font=font)
    image.save(directory / "thumbnail.png", optimize=True)
