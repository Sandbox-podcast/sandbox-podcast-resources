"""Generate local 5–15 minute YouTube packages without publishing anything."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import os
from pathlib import Path
import sys

from .shorts import _require_media_tools, _sha256
from .storage import digest, exclusive_run, save_json
from .thematic_analysis import PROMPT, analyze_local, analyze_openai
from .thematic_core import VERSION, edit_timeline, read_transcript, sentences, subtitles, validate_analysis
from .thematic_render import canvas, probe, render, thumbnail, verify


def quantize(timeline: list[dict], fps: str) -> list[dict]:
    rate, cursor = float(Fraction(fps)), 0.0
    for edit in timeline:
        frames = round((edit["source_end"]-edit["source_start"]) * rate)
        end = cursor + frames / rate
        edit.update(output_start=round(cursor, 6), output_end=round(end, 6), frames=frames)
        cursor = end
    if not 300 <= cursor <= 900:
        raise ValueError("Durée hors limites après alignement sur les images.")
    return timeline


def timestamp(seconds: float) -> str:
    total = round(seconds)
    return f"{total//3600:02}:{total//60%60:02}:{total%60:02}"


def write_report(directory: Path, manifest: dict) -> None:
    lines = ["# Vidéos thématiques Sandbox", "", f"État : {manifest['status']}. Analyse : {manifest['analyzer']}.", "",
             "Les notes servent au classement éditorial ; elles ne prédisent pas les vues.", "",
             "| Vidéo | Sujet | Durée | Score | Timecodes source du corps |",
             "| --- | --- | --- | --- | --- |"]
    for row in manifest["videos"]:
        ranges = ", ".join(f"{timestamp(a)}–{timestamp(b)}" for a, b in row["source_ranges"])
        lines.append(f"| {row['folder']} | {row['title'].replace('|', '/')} | {timestamp(row['duration'])} | {row['score']}/100 | {ranges} |")
    if not manifest["videos"] and manifest["status"] != "analysis_ready":
        lines += ["", "Aucun sujet admissible retenu. Aucun rendu artificiel pour atteindre un quota."]
    elif manifest["status"] == "analysis_ready":
        lines += ["", f"{manifest.get('selected_count', 0)} sujets retenus dans selection.json. Le rendu n’a pas encore été lancé."]
    lines += ["", "Chaque dossier contient MP4, SRT, miniature 1280 × 720, métadonnées, preuves éditoriales et montage.json.",
              "L’accroche reprend les paroles de l’émission, puis le corps les rejoue dans leur contexte.",
              "Les silences retirés sont des intervalles sans parole transcrite de plus de 1,8 seconde.",
              "Les limites fondées sur les pauses ASR et les sous-titres automatiques nécessitent une écoute avant publication.",
              "Le contrôle technique couvre le décodage complet, les dimensions et les horloges des pistes. Il ne certifie pas le sens d’un montage.",
              "Aucune publication, programmation ou modification de compte n’est exécutée."]
    if manifest["analyzer"] == "local":
        lines += ["", "L’analyse locale applique un vocabulaire et des marqueurs de discussion limités. Elle ne reconnaît pas tous les sujets d’une émission. L’analyse sémantique OpenAI est disponible séparément."]
    (directory / "rapport.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(source: Path, transcript: Path, output: Path, *, video_id: str | None = None,
        analyzer: str = "local", model: str = "", analysis: Path | None = None, count: int = 5,
        minimum: float = 72, burn: bool = False, analyze_only: bool = False) -> dict:
    source, transcript, output = source.resolve(strict=True), transcript.resolve(strict=True), output.resolve()
    if any(path.is_relative_to(output) for path in (source, transcript)):
        raise ValueError("Le dossier de sortie doit être distinct des médias et de la transcription source.")
    if analysis and analysis.resolve().is_relative_to(output):
        raise ValueError("Le fichier d'analyse fourni doit rester hors du dossier de sortie.")
    if video_id:
        from .identity import validate_video_id
        validate_video_id(video_id)
    ffmpeg, ffprobe = _require_media_tools()
    info = probe(source, ffprobe)
    width, height, fps = canvas(info)
    duration = float(info["format"]["duration"])
    source_hash = _sha256(source)
    segments = read_transcript(transcript, duration, video_id, source_hash)
    units = sentences(segments)
    validate_analysis({"candidates": []}, units, count, minimum)
    options = {"version": VERSION, "source_sha256": source_hash, "transcript_sha256": digest(segments),
               "analysis_sha256": _sha256(analysis) if analysis else None, "video_id": video_id,
               "analyzer": analyzer, "model": model if analyzer == "openai" else "", "prompt": digest(PROMPT),
               "count": count, "minimum": minimum, "burn_subtitles": burn}
    fingerprint = digest(options)
    state = output / "thematic-manifest.json"
    # Refuse to adopt a Shorts directory or somebody else's existing export folder.
    if output.exists() and not state.exists() and any(output.iterdir()):
        raise ValueError("Dossier non vide sans manifeste thématique. Choisissez un nouveau dossier.")
    with exclusive_run(output):
        if state.exists():
            manifest = json.loads(state.read_text(encoding="utf-8"))
            if manifest.get("kind") != "sandbox_thematic" or manifest.get("fingerprint") != fingerprint:
                raise ValueError("Source, transcription ou paramètres différents. Utilisez un nouveau dossier pour la révision.")
        else:
            manifest = {"kind": "sandbox_thematic", "fingerprint": fingerprint, "options": options, "analyzer": analyzer,
                        "source": str(source), "source_info": info, "status": "analyzing", "videos": [], "publication": "not_uploaded"}
            save_json(state, manifest)
        save_json(output / "transcript.json", {"source_sha256": source_hash, "segments": segments})
        save_json(output / "units.json", units)
        cache = output / "analysis.json"
        if cache.exists():
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if cached.get("fingerprint") != fingerprint or cached.get("raw_sha256") != digest(cached.get("raw")):
                raise ValueError("Cache d'analyse modifié ou lié à un autre lot.")
            raw = cached["raw"]
        else:
            print(f"Analyse {analyzer} : {len(segments)} segments, {len(units)} unités de parole…", flush=True)
            raw = json.loads(analysis.read_text(encoding="utf-8-sig")) if analysis else (
                analyze_openai(units, model) if analyzer == "openai" else analyze_local(units))
            validate_analysis(raw, units, count, minimum)
            save_json(cache, {"fingerprint": fingerprint, "raw_sha256": digest(raw), "raw": raw})
        plan = validate_analysis(raw, units, count, minimum)
        save_json(output / "selection.json", plan)
        if analyze_only:
            manifest["status"] = "analysis_ready"
            manifest["selected_count"] = len(plan["selected"])
            save_json(state, manifest)
            write_report(output, manifest)
            return {"status": "analysis_ready", "selected": len(plan["selected"]), "output": str(output)}
        records = []
        previous_records = {row["folder"]: row for row in manifest["videos"]}
        for index, candidate in enumerate(plan["selected"]):
            try:
                timeline = quantize(edit_timeline(candidate, units, segments), fps)
            except ValueError as error:
                plan["rejected"].append({**candidate, "rejection_reason": str(error)})
                continue
            name = f"video-{index+1:02}-{candidate['id']}"
            directory = output / name
            if not directory.resolve().is_relative_to(output):
                raise ValueError("Dossier vidéo hors de la destination autorisée.")
            directory.mkdir(exist_ok=True)
            length = timeline[-1]["output_end"]
            description = candidate["description"] + "\n\nSandbox Podcast, le talkshow sur l’IA et la tech avec Lou, Loïc et Nico."
            if video_id:
                description += f"\nÉmission complète : https://www.youtube.com/watch?v={video_id}"
            metadata = {**candidate, "description": description, "publication": "not_uploaded", "editorial_status": "needs_listening",
                        "transcript_status": "automatic", "hook_source": [units[candidate["hook"][0]]["start"], units[candidate["hook"][1]]["end"]]}
            (directory / "subtitles.srt").write_text(subtitles(timeline, segments), encoding="utf-8-sig")
            (directory / "titre.txt").write_text(candidate["title"] + "\n", encoding="utf-8")
            (directory / "description.txt").write_text(description + "\n", encoding="utf-8")
            save_json(directory / "metadata.json", metadata)
            previous = previous_records.get(name)
            if previous and (directory / "video.mp4").exists():
                if previous["technical"]["sha256"] != _sha256(directory / "video.mp4"):
                    raise ValueError("Un export final a été modifié. Conservez-le et choisissez un nouveau dossier.")
                checked = verify(directory / "video.mp4", length, (width, height), ffmpeg, ffprobe)
            else:
                print(f"Rendu {index+1}/{len(plan['selected'])} : {candidate['title']} ({length:.1f} s)…", flush=True)
                checked = render(source, directory, timeline, info, burn, ffmpeg, ffprobe)
            if not (directory / "thumbnail.png").exists():
                thumbnail(source, directory, candidate["thumbnail_text"], metadata["hook_source"][0], ffmpeg)
            save_json(directory / "montage.json", {"source_sha256": source_hash, "timeline": timeline, "technical": checked})
            records.append({"folder": name, "title": candidate["title"], "duration": length, "score": candidate["score"],
                            "source_ranges": [[units[a]["start"], units[b]["end"]] for a, b in candidate["ranges"]], "technical": checked})
            manifest.update(videos=records, status="rendering")
            save_json(state, manifest)
            write_report(output, manifest)
            print(f"Export vérifié : {directory / 'video.mp4'}", flush=True)
        save_json(output / "selection.json", plan)
        manifest.update(status="complete" if records else "no_suitable_topics", videos=records)
        save_json(state, manifest)
        write_report(output, manifest)
        return {"status": manifest["status"], "videos": len(records), "output": str(output), "publication": "not_uploaded"}


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Master ou copie Studio obtenue par le propriétaire.")
    parser.add_argument("--transcript", type=Path, required=True, help="JSON, JSONL, manifeste Shorts ou export texte YouTube existant.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--video-id")
    parser.add_argument("--analyzer", choices=("local", "openai"), default="local")
    parser.add_argument("--model", default=os.environ.get("YOUTUBE_THEMATIC_MODEL", ""))
    parser.add_argument("--analysis", type=Path, help="Analyse existante au même format que analysis.json/raw.")
    parser.add_argument("--count", type=int, choices=range(1, 6), default=5)
    parser.add_argument("--minimum-score", type=float, default=72)
    parser.add_argument("--burn-subtitles", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args(argv)
    return run(args.source, args.transcript, args.output, video_id=args.video_id, analyzer=args.analyzer, model=args.model,
               analysis=args.analysis, count=args.count, minimum=args.minimum_score, burn=args.burn_subtitles, analyze_only=args.analyze_only)


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False))
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
