"""Small FFmpeg slideshow renderer with provenance and explicit caption accuracy."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import textwrap
from uuid import uuid4

from .core import load_json, write_json
from .production import check_pack, fingerprint, probe


def srt_time(seconds):
    ms = round(seconds*1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def subtitles(board, voice):
    chunks = []
    alignment = voice.get("alignment")
    if alignment:
        chars, starts, ends = (alignment[k] for k in ("characters", "character_start_times_seconds", "character_end_times_seconds"))
        begin = 0
        for index, char in enumerate(chars):
            if index-begin >= 65 and char.isspace() or char in ".!?" or index == len(chars)-1:
                text = "".join(chars[begin:index+1]).strip()
                if text:
                    chunks.append((starts[begin], ends[index], text))
                begin = index+1
        accuracy = "elevenlabs_character_alignment_listening_pending"
    else:
        words = sum(len(s["narration"].split()) for s in board["scenes"])
        cursor = 0.
        for scene in board["scenes"]:
            for text in re.findall(r"[^.!?]+[.!?]?", scene["narration"]):
                duration = len(text.split())/words*voice["duration_seconds"]
                chunks.append((cursor, cursor+duration, text.strip()))
                cursor += duration
        accuracy = "estimated_word_proportions_not_transcribed"
    output = []
    for index, (start, end, text) in enumerate(chunks, 1):
        output.extend([str(index), srt_time(start)+" --> "+srt_time(end), "\n".join(textwrap.wrap(text, 48)), ""])
    return "\n".join(output), accuracy


def run(command, cwd, timeout=1800):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError("FFmpeg a échoué : "+result.stderr[-2000:])


def render(directory, *, allow_demo=False):
    directory = Path(directory).resolve()
    pack = check_pack(directory)
    board = load_json(directory / "storyboard.json")
    voice = load_json(directory / "audio" / "voice.json")
    audio_path = Path(voice["path"]).resolve(strict=True)
    if audio_path.parent != directory / "audio" or fingerprint(audio_path) != voice["sha256"] or voice["script_sha256"] != pack["script_sha256"]:
        raise ValueError("Narration modifiée ou liée à un autre script.")
    maximum = board.get("max_video_seconds", 300)
    if not (pack["synthetic"] and allow_demo) and not 120 <= voice["duration_seconds"] <= maximum:
        raise ValueError(f"Narration hors de 120..{maximum} secondes ; aucune troncature automatique.")
    output = directory / "render" / uuid4().hex[:12]
    output.mkdir(parents=True)
    caption_text, accuracy = subtitles(board, voice)
    (output / "captions.srt").write_text(caption_text, encoding="utf-8")
    shutil.copyfile(audio_path, output / ("voice"+audio_path.suffix))
    total_words = sum(len(s["narration"].split()) for s in board["scenes"])
    parts, cursor, evidence = [], 0., []
    for index, scene in enumerate(board["scenes"], 1):
        source = (directory / scene["asset"]).resolve(strict=True)
        if source.parent != directory / "assets" or fingerprint(source) != scene["asset_sha256"]:
            raise ValueError("Visuel absent, extérieur au pack ou modifié.")
        image = f"scene-{index:02d}.png"
        shutil.copyfile(source, output / image)
        seconds = len(scene["narration"].split())/total_words*voice["duration_seconds"]
        if seconds < .08:
            raise ValueError("Séquence trop courte.")
        part = f"part-{index:02d}.mp4"
        fade = min(.2, seconds/4)
        # The text is already rasterized from editable SVG; avoid drawtext quoting problems.
        filters = f"scale=1960:1102,crop=1920:1080:x='20+10*sin(t/4)':y=11,setsar=1,fade=t=in:st=0:d={fade},fade=t=out:st={max(0, seconds-fade)}:d={fade},format=yuv420p"
        run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-loop", "1", "-framerate", "25", "-i", image, "-t", f"{seconds:.6f}", "-vf", filters,
             "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-threads", "2", part], output)
        parts.append("file '"+part+"'")
        evidence.append({"scene": index, "start_seconds_estimate": cursor, "duration_seconds_estimate": seconds, "asset_sha256": scene["asset_sha256"]})
        cursor += seconds
    (output / "concat.txt").write_text("\n".join(parts)+"\n", encoding="utf-8")
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-f", "concat", "-safe", "1", "-i", "concat.txt", "-i", "voice"+audio_path.suffix,
         "-map", "0:v:0", "-map", "1:a:0", "-vf", "subtitles=captions.srt:force_style='FontSize=20,Outline=2,MarginV=30'", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-threads", "2",
         "-c:a", "aac", "-b:a", "192k", "-af", "alimiter=limit=0.89:level=false", "-t", str(voice["duration_seconds"]), "-movflags", "+faststart", "video.mp4"], output)
    final = output / "video.mp4"
    metadata = probe(final)
    video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    if (video["width"], video["height"]) != (1920, 1080) or not any(s["codec_type"] == "audio" for s in metadata["streams"]):
        raise ValueError("Export sans audio ou hors de 1080p.")
    if abs(float(metadata["format"]["duration"])-voice["duration_seconds"]) > .3:
        raise ValueError("Durée du rendu différente de la narration.")
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", "video.mp4", "-f", "null", "-"], output)
    receipt = {"path": str(final), "sha256": fingerprint(final), "audio_sha256": voice["sha256"], "script_sha256": pack["script_sha256"], "storyboard_sha256": pack["storyboard_sha256"],
               "synthetic": pack["synthetic"], "caption_accuracy": accuracy, "scene_timing": "word_proportion_estimate", "scenes": evidence,
               "technical_check": "1080p_audio_duration_full_decode_passed", "audiovisual_review": "pending", "ffmpeg_version": subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10).stdout.splitlines()[0]}
    write_json(output / "receipt.json", receipt)
    return receipt
