"""Local FFmpeg renders from an owned Studio download and reviewed shot choices."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from .editorial import parse_youtube_transcript
from .shorts import _call, _require_media_tools, _sha256, _subtitle_filter_path
from .storage import exclusive_run, save_json
from .identity import validate_video_id


def _ass_time(seconds: float) -> str:
    total = max(0, round(seconds * 100))
    hours, rest = divmod(total, 360000)
    minutes, rest = divmod(rest, 6000)
    seconds, centis = divmod(rest, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{centis:02}"


def _ass_text(text: str) -> str:
    return text.replace("\\", " ").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def subtitle_script(segments: list[dict], clip: dict) -> str:
    duration = clip["end"] - clip["start"]
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "", "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding", "Style: Caption,Arial,66,&H00FFFFFF,&H00FFFFFF,&H00221307,&H00221307,-1,0,0,0,100,100,0,0,1,4,0,2,80,120,280,1", "Style: Brand,Arial,46,&H00DEE842,&H00FFFFFF,&H00221307,&H00221307,-1,0,0,0,100,100,7,0,1,0,0,8,80,120,105,1", "Style: Title,Arial,72,&H00FFFFFF,&H00FFFFFF,&H00221307,&H00221307,-1,0,0,0,100,100,0,0,1,3,0,8,80,120,205,1", "Style: Footer,Arial,30,&H00DEE842,&H00FFFFFF,&H00221307,&H00221307,0,0,0,0,100,100,0,0,1,1,0,2,80,120,170,1", "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text", f"Dialogue: 0,0:00:00.00,{_ass_time(duration)},Brand,,0,0,0,,SANDBOX", f"Dialogue: 0,0:00:00.00,{_ass_time(duration)},Title,,0,0,0,,{_ass_text(clip['title'])}", f"Dialogue: 0,0:00:00.00,{_ass_time(duration)},Footer,,0,0,0,,La discussion complète sur SANDBOX"]
    for segment in segments:
        start = max(segment["start"], clip["start"])
        end = min(segment["end"], clip["end"])
        if end <= start:
            continue
        words = _ass_text(segment["text"]).split()
        index = 0
        while index < len(words):
            phrase = []
            while index+len(phrase) < len(words) and len(phrase) < 6:
                word = words[index+len(phrase)]
                if phrase and len(" ".join([*phrase, word])) > 32:
                    break
                phrase.append(word)
            chunk_start = start + (end-start) * index / len(words)
            chunk_end = start + (end-start) * (index+len(phrase)) / len(words)
            lines.append(f"Dialogue: 1,{_ass_time(chunk_start-clip['start'])},{_ass_time(chunk_end-clip['start'])},Caption,,0,0,0,,{' '.join(phrase)}")
            index += len(phrase)
    return "\n".join(lines) + "\n"


def layout_filter(layout: str) -> str:
    # Shot selections are explicit for episode 1. No claimed speaker diarization.
    if layout == "slide":
        return "[0:v]split=2[slide][person];[slide]scale=1000:562[slide];[person]crop=154:154:1094:535,scale=380:380,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(pow(X-W/2,2)+pow(Y-H/2,2),pow(W/2-2,2)),255,0)'[person];color=c=0x071322:s=1080x1920:r=24[base];[base][slide]overlay=20:440[a];[a][person]overlay=330:1050[frame]"
    if layout == "panel":
        return "[0:v]split=3[hero][r1][r2];[hero]crop=346:240:934:480,scale=1000:694[hero];[r1]crop=346:240:934:0,scale=480:333[r1];[r2]crop=346:240:934:240,scale=480:333[r2];color=c=0x071322:s=1080x1920:r=24[base];[base][hero]overlay=20:420[a];[a][r1]overlay=20:1160[b];[b][r2]overlay=550:1160[frame]"
    if layout == "speaker":
        return "[0:v]split=3[hero][r1][r2];[hero]crop=886:500:24:110,scale=1000:564[hero];[r1]crop=340:236:934:242,scale=490:340[r1];[r2]crop=340:236:934:482,scale=490:340[r2];color=c=0x071322:s=1080x1920:r=24[base];[base][hero]overlay=20:440[a];[a][r1]overlay=20:1060[b];[b][r2]overlay=530:1060[frame]"
    if layout == "fit":
        return "[0:v]scale=1000:562[video];color=c=0x071322:s=1080x1920:r=24[base];[base][video]overlay=20:600[frame]"
    raise ValueError("Disposition inconnue. Choisissez slide, panel, speaker ou fit après inspection de la source.")


def validate_render_pack(pack: object) -> dict:
    if not isinstance(pack, dict) or pack.get("version") != 1 or not isinstance(pack.get("source_video_id"), str):
        raise ValueError("Dossier de rendu non conforme.")
    validate_video_id(pack["source_video_id"])
    duration = pack.get("source_duration")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Durée de source invalide.")
    clips = pack.get("candidates")
    if not isinstance(clips, list) or not 1 <= len(clips) <= 10:
        raise ValueError("Liste de candidats invalide.")
    identities = set()
    for clip in clips:
        if not isinstance(clip, dict) or not re.fullmatch(r"[a-f0-9]{16}", str(clip.get("id", ""))):
            raise ValueError("Identifiant de clip invalide.")
        if clip["id"] in identities:
            raise ValueError("Clip dupliqué dans le dossier.")
        identities.add(clip["id"])
        for field in ("start", "end", "duration"):
            value = clip.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Horodatages de rendu invalides.")
        if not 0 <= clip["start"] < clip["end"] <= duration or not 5 <= clip["duration"] <= 180 or abs(clip["duration"]-(clip["end"]-clip["start"])) > 0.001:
            raise ValueError("Durée de clip incohérente.")
        if not isinstance(clip.get("selected"), bool) or not isinstance(clip.get("title"), str) or not 1 <= len(clip["title"]) <= 100:
            raise ValueError("Sélection et titre du clip invalides.")
        layout_filter(clip.get("layout", "fit"))
    return pack


def check_render_directory(directory: Path, video_id: str, source_hash: str) -> None:
    manifest = directory / "render-manifest.json"
    if not manifest.exists():
        return
    previous = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if not isinstance(previous, dict) or not isinstance(previous.get("clips"), list):
        raise ValueError("Le manifeste existant est invalide. Conservez-le pour vérifier les opérations précédentes.")
    if previous.get("source_video_id") != video_id or previous.get("source_sha256") != source_hash:
        raise ValueError("Ce dossier contient les rendus d'une autre source. Choisissez un nouveau dossier.")
    if any(not isinstance(clip, dict) for clip in previous["clips"]):
        raise ValueError("Le manifeste existant contient un clip invalide.")
    if any(clip.get("youtube_video_id") or clip.get("upload_started") for clip in previous["clips"]):
        raise RuntimeError("Un rendu de ce dossier est déjà téléversé ou son upload est incertain. Utilisez un nouveau dossier pour une révision; conservez les identifiants YouTube existants.")


def render_pack(source: Path, transcript: Path, pack_path: Path, directory: Path) -> dict:
    ffmpeg, ffprobe = _require_media_tools()
    pack = validate_render_pack(json.loads(pack_path.read_text(encoding="utf-8")))
    info = json.loads(_call([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(source)]))
    duration = float(info["format"]["duration"])
    streams = info["streams"]
    if not any(s.get("codec_type") == "audio" for s in streams) or not any(s.get("width") == 1280 and s.get("height") == 720 for s in streams):
        raise ValueError("Ces cadrages ont été vérifiés sur une source 1280 x 720 avec audio. Revoyez les cadrages pour une autre source.")
    if abs(duration-pack["source_duration"]) > 2:
        raise ValueError("La durée de la copie ne correspond pas à l'émission du dossier.")
    segments = parse_youtube_transcript(transcript.read_text(encoding="utf-8-sig"), pack["source_video_id"], duration)
    source_hash = _sha256(source)
    result = {"source_video_id": pack["source_video_id"], "source_sha256": source_hash, "source_path": str(source.resolve()), "source_origin": "Fichier local fourni à la commande; voir les preuves de provenance du dossier de livraison", "subtitles_status": "automatic_needs_listening", "clips": []}
    with exclusive_run(directory):
        check_render_directory(directory, pack["source_video_id"], source_hash)
        for clip in pack["candidates"]:
            if not clip["selected"]:
                continue
            ass_path = directory / f"{clip['id']}.ass"
            output = directory / f"{clip['id']}.mp4"
            if output.resolve() == source.resolve():
                raise ValueError("Le rendu ne peut pas remplacer la source.")
            ass_path.write_text(subtitle_script(segments, clip), encoding="utf-8-sig")
            layout = clip.get("layout", "fit")
            video_filter = layout_filter(layout) + f";[frame]ass=filename='{_subtitle_filter_path(ass_path)}'[out]"
            temporary = output.with_suffix(".partial.mp4")
            _call([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(clip["start"]), "-i", str(source), "-filter_complex", video_filter, "-map", "[out]", "-map", "0:a:0", "-t", str(clip["duration"]), "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temporary)])
            checked = json.loads(_call([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(temporary)]))
            if abs(float(checked["format"]["duration"])-clip["duration"]) > 0.2 or not any(s.get("width") == 1080 and s.get("height") == 1920 for s in checked["streams"]):
                raise RuntimeError("Le rendu ne respecte pas sa durée ou sa résolution.")
            # Decode the complete exported file before claiming it rendered correctly.
            _call([ffmpeg, "-v", "error", "-xerror", "-i", str(temporary), "-f", "null", "-"])
            temporary.replace(output)
            result["clips"].append({**clip, "file": str(output.resolve()), "ass": str(ass_path.resolve()), "render_sha256": _sha256(output), "technical_status": "decoded", "editorial_status": "needs_review", "youtube_video_id": None})
            save_json(directory / "render-manifest.json", result)
            print(f"Rendu vérifié : {output}", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Rend les extraits sélectionnés depuis une copie obtenue dans Studio")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render_pack(args.source, args.transcript, args.pack, args.output)


if __name__ == "__main__":
    main()
