"""Local, traceable media jobs. No social clients or paid model calls."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from ..shorts import _call, _require_media_tools, _sha256, _subtitle_filter_path
from ..storage import digest, save_json
from ..thematic_core import read_transcript
from ..thematic_render import probe as _probe
from .local_lock import local_lock as exclusive_run

VERSION = 1


def fingerprint(path: Path) -> str:
    return _sha256(Path(path).resolve(strict=True))


def probe(source: Path) -> dict:
    """Inspect a local, complete source without changing it."""
    _, ffprobe = _require_media_tools()
    info = _probe(Path(source).resolve(strict=True), ffprobe)
    duration = float(info.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Durée du média invalide.")
    if not any(s.get("codec_type") == "video" for s in info.get("streams", [])):
        raise ValueError("La source ne contient aucune piste vidéo.")
    if not any(s.get("codec_type") == "audio" for s in info["streams"]):
        raise ValueError("La source ne contient aucune piste audio.")
    return {**info, "duration_seconds": duration}


def _scan(path: Path) -> dict:
    """Decode every frame/sample; technical detection is not semantic review."""
    ffmpeg, _ = _require_media_tools()
    command = [ffmpeg, "-nostdin", "-hide_banner", "-v", "info", "-xerror", "-i", str(path),
               "-map", "0:v:0", "-map", "0:a:0", "-vf", "blackdetect=d=1:pix_th=0.03:pic_th=0.98",
               "-af", "silencedetect=noise=-45dB:d=2,volumedetect", "-f", "null", "-"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError("Décodage intégral impossible : " + result.stderr[-1200:])
    log = result.stderr
    return {"decode": "passed", "scope": "complete_technical_decode",
            "black_intervals_seconds": [{"start": float(a), "end": float(b)} for a, b in
                                        re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)],
            "silence_events": [line.split("silencedetect", 1)[-1].split("]", 1)[-1].strip()
                               for line in log.splitlines() if "silence_start:" in line or "silence_end:" in line],
            "max_volume_db": next((float(v) for v in re.findall(r"max_volume: ([-\d.]+) dB", log)), None),
            "synchronization": "container_timestamps_only"}


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _ranges(value: object, duration: float) -> list[list[float]]:
    if not isinstance(value, list):
        raise ValueError("Les intervalles de couverture doivent être une liste en secondes.")
    ranges = []
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2 or not all(_number(n) for n in pair):
            raise ValueError("Intervalle de couverture invalide.")
        if not 0 <= pair[0] < pair[1] <= duration + .1:
            raise ValueError("Couverture hors du média source.")
        ranges.append([float(pair[0]), min(duration, float(pair[1]))])
    return ranges


def _covered(ranges: list[list[float]], start: float, end: float) -> bool:
    cursor = start
    for a, b in sorted(ranges):
        if a > cursor + .1:
            break
        cursor = max(cursor, b)
        if cursor >= end - .1:
            return True
    return False


def _coverage(ranges: list[list[float]], duration: float) -> dict:
    merged = []
    for a, b in sorted(ranges):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    seconds = sum(b-a for a, b in merged)
    gaps, cursor = [], 0.0
    for a, b in merged:
        if a > cursor + .1:
            gaps.append([cursor, a])
        cursor = b
    if cursor < duration - .1:
        gaps.append([cursor, duration])
    return {"ranges_seconds": merged, "covered_seconds": round(seconds, 3),
            "fraction": round(seconds / duration, 5), "unexamined_ranges_seconds": gaps,
            "complete": not gaps}


def _cuts(candidate: dict, duration: float) -> list[dict]:
    raw = candidate.get("cuts")
    if raw is None:
        raw = [{"source_start_seconds": candidate.get("start_seconds"),
                "source_end_seconds": candidate.get("end_seconds")}]
    if not isinstance(raw, list) or not raw or len(raw) > 100:
        raise ValueError("Une à cent coupes source sont requises.")
    cuts, cursor, previous = [], 0.0, -1.0
    for item in raw:
        a, b = item.get("source_start_seconds"), item.get("source_end_seconds")
        if not _number(a) or not _number(b) or not 0 <= a < b <= duration + .02 or a < previous:
            raise ValueError("Coupes invalides, superposées ou hors ordre chronologique.")
        length = min(b, duration) - a
        cuts.append({"source_start_seconds": float(a), "source_end_seconds": float(min(b, duration)),
                     "output_start_seconds": round(cursor, 6), "output_end_seconds": round(cursor+length, 6)})
        cursor += length
        previous = b
    return cuts


def _frames(source: Path, output: Path, duration: float) -> list[dict]:
    ffmpeg, _ = _require_media_tools()
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    # Explicit point samples: no claim that the intervals between them were watched.
    count = min(12, max(2, math.ceil(duration / 60)))
    for index in range(count):
        at = min(duration-.05, duration * (index+.5) / count)
        frame = output / f"source-frame-{index:02}.jpg"
        if not frame.exists():
            _call([ffmpeg, "-nostdin", "-v", "error", "-n", "-ss", str(at), "-i", str(source),
                   "-frames:v", "1", "-vf", "scale=640:-2", str(frame)])
        rows.append({"time_seconds": round(at, 3), "path": str(frame.resolve()), "sha256": fingerprint(frame)})
    try:
        from PIL import Image, ImageDraw
        sheet = Image.new("RGB", (1280, math.ceil(count/2)*385), "#071322")
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(rows):
            with Image.open(row["path"]) as raw:
                raw.thumbnail((640, 360))
                sheet.paste(raw, ((i % 2)*640, (i // 2)*385))
            draw.text(((i % 2)*640+8, (i // 2)*385+363), f"Source {row['time_seconds']:.3f} s", fill="white")
        sheet.save(output / "contact-sheet.jpg")
    except ImportError:
        pass
    return rows


def analyze(source: Path, transcript: Path | None, output: Path, *, evidence: Path | None = None) -> dict:
    """Read every supplied transcript segment and record actual modality coverage.

    Offline semantic decisions require a versioned review evidence file. Missing
    models/credentials do not silently become heuristic editorial decisions.
    """
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    if source.is_relative_to(output):
        raise ValueError("La source doit rester hors du dossier d'analyse.")
    source_hash, info = fingerprint(source), probe(source)
    duration = info["duration_seconds"]
    transcript = Path(transcript).resolve(strict=True) if transcript else None
    evidence = Path(evidence).resolve(strict=True) if evidence else None
    if any(p.is_relative_to(output) for p in (transcript, evidence) if p):
        raise ValueError("Les entrées d'analyse doivent rester hors du dossier de sortie.")
    identity = {"version": VERSION, "source_sha256": source_hash,
                "transcript_sha256": fingerprint(transcript) if transcript else None,
                "evidence_sha256": fingerprint(evidence) if evidence else None}
    key = digest(identity)
    output.mkdir(parents=True, exist_ok=True)
    cache = output / f"analysis-{key}.json"
    if cache.exists():
        previous = json.loads(cache.read_text(encoding="utf-8"))
        if previous.get("cache_key") != key:
            raise ValueError("Reçu d'analyse incompatible.")
        return previous
    with exclusive_run(output):
        segments = read_transcript(transcript, duration, source_hash=source_hash) if transcript else []
        transcript_ranges = [[s["start"], s["end"]] for s in segments]
        raw = json.loads(evidence.read_text(encoding="utf-8-sig")) if evidence else {}
        if raw and (raw.get("version") != 1 or raw.get("source_sha256") != source_hash):
            raise ValueError("L'analyse éditoriale ne correspond pas au master.")
        provenance = raw.get("provenance", {})
        fixture = provenance.get("kind") == "fixture"
        coverage_raw = raw.get("coverage", {})
        modality_ranges = {k: _ranges(coverage_raw.get(k+"_ranges_seconds", []), duration)
                           for k in ("audio", "visual", "transcript")}
        technical_path = output / f"technical-{source_hash}.json"
        technical = json.loads(technical_path.read_text(encoding="utf-8")) if technical_path.exists() else _scan(source)
        save_json(technical_path, technical)
        frame_dir = output / f"frames-{source_hash[:20]}"
        samples = _frames(source, frame_dir, duration)
        candidates, rejected = [], []
        for index, row in enumerate(raw.get("candidates", [])):
            try:
                if not isinstance(row, dict):
                    raise ValueError("Candidat non structuré.")
                cuts = _cuts(row, duration)
                if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("title", "audience", "rationale")):
                    raise ValueError("Titre, public et justification éditoriale requis.")
                decision = row.get("decision", "needs_review")
                if decision not in {"retained", "needs_review", "rejected", "archived"}:
                    raise ValueError("Décision éditoriale inconnue.")
                risks = list(row.get("risks", []))
                reviewed = all(_covered(modality_ranges[k], cut["source_start_seconds"], cut["source_end_seconds"])
                               for cut in cuts for k in ("audio", "visual", "transcript"))
                if decision == "retained" and (not reviewed or provenance.get("kind") not in {"human_review", "fixture"}):
                    decision = "needs_review"
                    risks.append("Revue sémantique multimodale absente ou incomplète.")
                candidate = {**row, "segment_id": "segment-"+digest({"source": source_hash, "cuts": cuts})[:16],
                             "source_sha256": source_hash, "start_seconds": cuts[0]["source_start_seconds"],
                             "end_seconds": cuts[-1]["source_end_seconds"], "cuts": cuts, "decision": decision,
                             "risks": risks, "synthetic": fixture,
                             "review_evidence_sha256": identity["evidence_sha256"]}
                candidates.append(candidate)
            except (ValueError, TypeError, AttributeError) as error:
                rejected.append({"candidate_index": index, "decision": "blocked", "reason": str(error)})
        blockers = []
        if not transcript:
            blockers.append("Transcription absente : aucune transcription automatique lancée sans moteur configuré.")
        if not evidence:
            blockers.append("Sélection éditoriale et reconnaissance des intervenants à fournir ; aucun modèle configuré.")
        for kind in ("audio", "visual", "transcript"):
            if not _coverage(modality_ranges[kind], duration)["complete"]:
                blockers.append(f"Revue sémantique {kind} incomplète ; ne pas annoncer un examen intégral.")
        result = {**identity, "cache_key": key, "duration_seconds": duration, "source": str(source),
                  "source_info": info, "synthetic": fixture, "provenance": provenance,
                  "coverage": {"transcript": {**_coverage(transcript_ranges, duration), "segments_read": len(segments),
                                              "scope": "all_supplied_text", "semantic_review": _coverage(modality_ranges["transcript"], duration)},
                               "audio": {"technical": "complete", "semantic_review": _coverage(modality_ranges["audio"], duration)},
                               "visual": {"technical": "complete_decode", "samples": samples,
                                          "semantic_review": _coverage(modality_ranges["visual"], duration),
                                          "sample_notice": "Images ponctuelles ; les intervalles entre images ne sont pas déclarés visionnés."}},
                  "speakers": raw.get("speakers", []), "speaker_identification": raw.get("speaker_identification", "unavailable"),
                  "candidates": candidates, "rejected_inputs": rejected, "technical": technical,
                  "artifacts": {"analysis": str(cache), "contact_sheet": str(frame_dir / "contact-sheet.jpg"),
                                "technical": str(technical_path)}, "blockers": blockers}
        if fingerprint(source) != source_hash:
            raise ValueError("Le master a changé pendant l'analyse ; résultats non validés.")
        save_json(cache, result)
        return result


def _srt_time(seconds: float) -> str:
    total = round(seconds*1000)
    return f"{total//3600000:02}:{total//60000%60:02}:{total//1000%60:02},{total%1000:03}"


def _subtitles(segments: list[dict], cuts: list[dict]) -> str:
    lines, index = [], 1
    for cut in cuts:
        for row in segments:
            start, end = max(row["start"], cut["source_start_seconds"]), min(row["end"], cut["source_end_seconds"])
            if end <= start:
                continue
            if row["start"] < cut["source_start_seconds"]-.001 or row["end"] > cut["source_end_seconds"]+.001:
                # Segment-level timestamps cannot say which words survived a cut.
                # Omit that cue and report the missing alignment rather than show
                # words that the exported audio may not contain.
                continue
            a = cut["output_start_seconds"] + start-cut["source_start_seconds"]
            b = cut["output_start_seconds"] + end-cut["source_start_seconds"]
            # No rewriting of the spoken text; mobile wrapping only.
            import textwrap
            text = "\n".join(textwrap.wrap(row["text"], width=38))
            lines += [str(index), f"{_srt_time(a)} --> {_srt_time(b)}", text, ""]
            index += 1
    return "\n".join(lines)


def _ass_subtitles(segments: list[dict], cuts: list[dict], size: tuple[int, int], vertical: bool) -> str:
    from ..rendering import _ass_time, _ass_text
    import textwrap
    width, height = size
    fontsize, side, bottom = (62, 100, 280) if vertical else (max(18, round(width/32)), 35, 35)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
             "WrapStyle: 0", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Caption,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00221307,&H00221307,-1,0,0,0,100,100,0,0,1,3,0,2,{side},{side+20},{bottom},1", "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for cut in cuts:
        for row in segments:
            start, end = max(row["start"], cut["source_start_seconds"]), min(row["end"], cut["source_end_seconds"])
            if end <= start:
                continue
            if row["start"] < cut["source_start_seconds"]-.001 or row["end"] > cut["source_end_seconds"]+.001:
                continue
            a = cut["output_start_seconds"] + start-cut["source_start_seconds"]
            b = cut["output_start_seconds"] + end-cut["source_start_seconds"]
            text = "\\N".join(_ass_text(line) for line in textwrap.wrap(row["text"], width=26 if vertical else 48))
            lines.append(f"Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Caption,,0,0,0,,{text}")
    return "\n".join(lines)+"\n"


def render(source: Path, candidate: dict, output: Path, *, format: str = "vertical",
           transcript: Path | None = None, fixture: bool = False) -> dict:
    """Render immutable, content-addressed outputs; title changes reuse the media."""
    if format not in {"vertical", "horizontal"}:
        raise ValueError("Format attendu : vertical ou horizontal.")
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    if source.is_relative_to(output):
        raise ValueError("La source doit rester hors du dossier de rendu.")
    transcript = Path(transcript).resolve(strict=True) if transcript else None
    if transcript and transcript.is_relative_to(output):
        raise ValueError("La transcription doit rester hors du dossier de rendu.")
    source_hash, info = fingerprint(source), probe(source)
    if candidate.get("source_sha256", source_hash) != source_hash:
        raise ValueError("La sélection ne correspond pas au master.")
    cuts = _cuts(candidate, info["duration_seconds"])
    length = cuts[-1]["output_end_seconds"]
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    if video.get("sample_aspect_ratio") not in {None, "1:1", "N/A"}:
        raise ValueError("Pixels source non carrés : fournir une copie normalisée sans modifier les timecodes.")
    size = (1080, 1920) if format == "vertical" else (max(32, min(1280, video["width"])//32*32), max(18, min(720, video["width"]*9/16)//18*18))
    options = {"version": VERSION, "source_sha256": source_hash, "cuts": cuts, "format": format,
               "size": size, "transcript_sha256": fingerprint(transcript) if transcript else None,
               "audio": "loudnorm-I-16-TP-1.5", "layout": "fit_preserve_all_pixels", "synthetic": fixture}
    key = digest(options)
    directory = output / key[:20]
    receipt = directory / "asset.json"
    if receipt.exists():
        previous = json.loads(receipt.read_text(encoding="utf-8"))
        if previous.get("cache_key") != key or any(fingerprint(Path(previous[k])) != previous[h]
                for k, h in (("path", "sha256"), ("master_path", "master_sha256"),
                             ("subtitle_path", "subtitle_sha256"), ("ass_path", "ass_sha256"))):
            raise ValueError("Un export terminé a été modifié. Aucun écrasement automatique.")
        return previous
    ffmpeg, _ = _require_media_tools()
    directory.mkdir(parents=True, exist_ok=True)
    with exclusive_run(directory):
        if transcript:
            segments = read_transcript(transcript, info["duration_seconds"], source_hash=source_hash)
        else:
            segments = []
        subtitle_path = directory / "subtitles.srt"
        ass_path = directory / "subtitles.ass"
        srt = _subtitles(segments, cuts)
        boundary_warnings = [{"source_start_seconds": row["start"], "source_end_seconds": row["end"],
                              "reason": "Coupe dans un segment de parole ; sous-titre omis faute d'alignement mot à mot."}
                             for cut in cuts for row in segments
                             if row["end"] > cut["source_start_seconds"] and row["start"] < cut["source_end_seconds"]
                             and (row["start"] < cut["source_start_seconds"]-.001 or row["end"] > cut["source_end_seconds"]+.001)]
        subtitle_path.write_text(srt, encoding="utf-8-sig")
        ass_path.write_text(_ass_subtitles(segments, cuts, size, format == "vertical"), encoding="utf-8-sig")
        inputs, filters, labels = [], [], []
        for index, cut in enumerate(cuts):
            duration = cut["output_end_seconds"]-cut["output_start_seconds"]
            inputs += ["-ss", str(cut["source_start_seconds"]), "-t", str(duration), "-i", str(source)]
            filters += [f"[{index}:v:0]trim=duration={duration},setpts=PTS-STARTPTS,scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2:color=0x071322,setsar=1[v{index}]",
                        f"[{index}:a:0]atrim=duration={duration},asetpts=PTS-STARTPTS,aresample=48000[a{index}]"]
            labels.append(f"[v{index}][a{index}]")
        filters += ["".join(labels)+f"concat=n={len(cuts)}:v=1:a=1[v][a]", "[a]loudnorm=I=-16:TP=-1.5:LRA=11[audio]"]
        master, final = directory / "master-clean.mp4", directory / "video.mp4"
        temporary = directory / "master.partial.mp4"
        master_receipt = directory / "master-stage.json"
        if master_receipt.exists():
            stage = json.loads(master_receipt.read_text(encoding="utf-8"))
            present = master if master.exists() else temporary
            if stage.get("cache_key") != key or not present.exists() or fingerprint(present) != stage.get("sha256"):
                raise ValueError("Master intermédiaire modifié ou perdu ; aucun écrasement automatique.")
            if present != master:
                temporary.replace(master)
        elif master.exists():
            raise ValueError("Master sans reçu déjà présent ; conserver le dossier pour diagnostic.")
        else:
            # Only an incomplete temporary file may be replaced after interruption.
            _call([ffmpeg, "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                   "-map", "[v]", "-map", "[audio]", "-t", str(length), "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", str(temporary)])
            save_json(master_receipt, {"cache_key": key, "sha256": fingerprint(temporary)})
            temporary.replace(master)
        final_stage, temporary = directory / "video-stage.json", directory / "video.partial.mp4"
        if final_stage.exists():
            stage = json.loads(final_stage.read_text(encoding="utf-8"))
            present = final if final.exists() else temporary
            if stage.get("cache_key") != key or not present.exists() or fingerprint(present) != stage.get("sha256"):
                raise ValueError("Rendu intermédiaire modifié ou perdu ; aucun écrasement automatique.")
            if present != final:
                temporary.replace(final)
        elif final.exists():
            raise ValueError("Rendu sans reçu déjà présent ; conserver le dossier pour diagnostic.")
        else:
            if srt:
                _call([ffmpeg, "-nostdin", "-v", "error", "-y", "-i", str(master), "-vf",
                       f"ass=filename='{_subtitle_filter_path(ass_path)}'", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", str(temporary)])
            else:
                shutil.copyfile(master, temporary)
            save_json(final_stage, {"cache_key": key, "sha256": fingerprint(temporary)})
            temporary.replace(final)
        technical = _scan(final)
        actual = probe(final)
        final_video = next(s for s in actual["streams"] if s["codec_type"] == "video")
        final_audio = next(s for s in actual["streams"] if s["codec_type"] == "audio")
        if abs(actual["duration_seconds"]-length) > .3 or (final_video["width"], final_video["height"]) != size:
            raise RuntimeError("La durée ou la résolution du rendu ne correspond pas au plan.")
        if final_video["codec_name"] != "h264" or final_audio["codec_name"] != "aac":
            raise RuntimeError("Codecs de rendu non conformes.")
        av_delta = abs(float(final_video.get("duration", length))-float(final_audio.get("duration", length)))
        if av_delta > .2:
            raise RuntimeError("Décalage de durée des pistes audio/vidéo.")
        samples = _frames(final, directory, length)
        qa_status = "passed" if not technical["black_intervals_seconds"] and not technical["silence_events"] else "needs_review"
        if technical["max_volume_db"] is None or technical["max_volume_db"] > -.1:
            qa_status = "needs_review"
        result = {"asset_id": "asset-"+key[:20], "version": 1, "cache_key": key, "path": str(final),
                  "sha256": fingerprint(final), "master_path": str(master), "master_sha256": fingerprint(master),
                  "source_sha256": source_hash, "segment_id": candidate.get("segment_id"), "format": format,
                  "duration_seconds": actual["duration_seconds"], "width": size[0], "height": size[1], "cuts": cuts,
                  "synthetic": fixture, "subtitle_path": str(subtitle_path), "subtitle_sha256": fingerprint(subtitle_path),
                  "ass_path": str(ass_path), "ass_sha256": fingerprint(ass_path),
                  "parameters": options, "frames": samples, "contact_sheet": str(directory / "contact-sheet.jpg"),
                  "qa": {"technical": qa_status, "details": technical, "av_duration_delta_seconds": round(av_delta, 5),
                         "visual": "pending_human_review", "audio": "pending_listening", "editorial": "pending_review",
                         "subtitles": "needs_word_alignment" if boundary_warnings else ("pending_review" if srt else "missing"),
                         "subtitle_boundary_warnings": boundary_warnings, "quality_revision_sha256": fingerprint(final)},
                  "publication": "not_uploaded"}
        if fingerprint(source) != source_hash:
            raise ValueError("Le master a changé pendant le rendu ; export non validé.")
        save_json(receipt, result)
        return result


def create_fixture(output: Path) -> dict:
    """Generate a 312-second synthetic local test source, never Sandbox speech."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "fixture.json"
    if manifest.exists():
        result = json.loads(manifest.read_text(encoding="utf-8"))
        if fingerprint(Path(result["source"])) != result["source_sha256"]:
            raise ValueError("Source de fixture modifiée.")
        return result
    ffmpeg, _ = _require_media_tools()
    source = output / "synthetic-fixture.mp4"
    if source.exists():
        raise ValueError("Fixture sans reçu déjà présente ; ne pas écraser le média.")
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (640, 360), "#071322")
    draw = ImageDraw.Draw(image)
    draw.rectangle((25, 25, 615, 335), outline="#00d5eb", width=4)
    draw.text((45, 80), "FIXTURE SYNTHETIQUE - SANDBOX", fill="white", font_size=26)
    draw.text((45, 135), "Image de test et sinus 440 Hz", fill="#00d5eb", font_size=22)
    draw.text((45, 185), "Aucune parole, aucun animateur", fill="white", font_size=22)
    draw.text((45, 245), "Duree : 312 secondes", fill="white", font_size=22)
    still = output / "fixture-card.png"
    image.save(still)
    _call([ffmpeg, "-nostdin", "-v", "error", "-n", "-loop", "1", "-framerate", "5", "-i", str(still),
           "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=312", "-t", "312", "-c:v", "libx264",
           "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", str(source)])
    source_hash = fingerprint(source)
    transcript = output / "synthetic-transcript.json"
    segments = [{"start": float(a), "end": float(min(a+12, 312)), "text": "[FIXTURE] Signal de test, aucune parole réelle."}
                for a in range(0, 312, 12)]
    save_json(transcript, {"source_sha256": source_hash, "synthetic": True, "segments": segments})
    evidence = output / "synthetic-evidence.json"
    save_json(evidence, {"version": 1, "source_sha256": source_hash, "synthetic": True,
                        "provenance": {"kind": "fixture", "reviewer": "synthetic_generator", "prompt_version": "fixture-v1"},
                        "coverage": {kind+"_ranges_seconds": [[0, 312]] for kind in ("audio", "visual", "transcript")},
                        "candidates": [{"title": "Fixture synthétique 12 secondes", "start_seconds": 0, "end_seconds": 12,
                                        "format": "vertical", "audience": "Vérification du pipeline", "rationale": "Vérifier un micro-extrait de 12 secondes.",
                                        "decision": "retained", "risks": ["Source synthétique sans parole."], "platforms": ["youtube", "tiktok", "instagram", "x", "linkedin"]},
                                       {"title": "Fixture synthétique 5 minutes", "start_seconds": 12, "end_seconds": 312,
                                        "format": "horizontal", "audience": "Vérification du pipeline", "rationale": "Vérifier un extrait développé de 300 secondes.",
                                        "decision": "retained", "risks": ["Source synthétique sans parole."], "platforms": ["youtube"]}]})
    result = {"synthetic": True, "source": str(source), "source_sha256": source_hash,
              "transcript": str(transcript), "evidence": str(evidence), "duration_seconds": 312,
              "notice": "Fixture technique ; aucune performance et aucun verbatim Sandbox.",
              "generation": "python -m youtube_growth.factory demo --help"}
    save_json(manifest, result)
    return result
