"""One bounded output-headroom repair, preserving source and encoded pictures."""
from __future__ import annotations

import copy
import math
import re
import subprocess
from pathlib import Path

from .contracts import digest
from .local_lock import local_lock
from .media import _load_stage, _save_stage, _scan, _frames, fingerprint, probe
from ..shorts import _call, _require_media_tools

HEADROOM_VERSION = 2


def decoded_peak(path: Path) -> float:
    """Measure floating-point AAC samples; volumedetect clamps peaks above 0 dB."""
    ffmpeg, _ = _require_media_tools()
    scan = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-nostats', '-i', str(path), '-vn',
                           '-af', 'astats=metadata=0:reset=0', '-f', 'null', '-'],
                          check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = scan.stderr
    values = [float(v) for v in re.findall(r'Peak level dB: ([-\d.]+)', log)]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError('Pic audio flottant indisponible ; aucune correction devinée.')
    return max(values)


def repair_headroom(asset: dict) -> dict:
    if asset.get("audio_headroom"):
        raise ValueError("Une seule correction automatique de marge audio est autorisée.")
    paths = {name: {"path": asset[name], "sha256": fingerprint(Path(asset[name]))} for name in ("path", "master_path", "subtitle_path", "ass_path")}
    if any(paths[k]["sha256"] != asset[h] for k,h in (("path","sha256"),("master_path","master_sha256"),
                                                      ("subtitle_path","subtitle_sha256"),("ass_path","ass_sha256"))):
        raise ValueError("Média changé avant correction audio.")
    peaks = {name: decoded_peak(Path(asset[name])) for name in ('path', 'master_path')}
    gain = -math.ceil(max(1.5, max(peaks.values())+1.5)*100)/100
    identity = {"stage": "output_headroom", "version": HEADROOM_VERSION, "inputs": paths,
                "source_sha256": asset["source_sha256"], "gain_db": gain, 'decoded_input_peaks_db': peaks}
    key = digest(identity)
    directory = Path(asset["path"]).parent.parent / ("headroom-"+key[:20])
    receipt = directory / "repair.json"
    previous = _load_stage(receipt, identity)
    if previous is not None:
        if any(fingerprint(Path(previous[k])) != previous[h] for k, h in (("path", "sha256"), ("master_path", "master_sha256"))):
            raise ValueError("Export audio corrigé modifié.")
        return previous
    directory.mkdir(parents=True, exist_ok=True)
    ffmpeg, _ = _require_media_tools()
    with local_lock(directory):
        outputs = {}
        for name, filename in (("master_path", "master-clean.mp4"), ("path", "video.mp4")):
            target = directory / filename
            partial = target.with_name(target.stem+".partial.mp4")
            stage = directory / (name+"-stage.json")
            stage_key = {**identity, "artifact": name}
            cached = _load_stage(stage, stage_key)
            if cached:
                present = target if target.exists() else partial
                if not present.exists() or fingerprint(present) != cached["sha256"]:
                    raise ValueError("Intermédiaire audio corrigé perdu ou modifié.")
                if present != target:partial.replace(target)
            elif target.exists():
                raise ValueError("Export corrigé sans reçu ; aucun écrasement.")
            else:
                _call([ffmpeg, "-nostdin", "-v", "error", "-y", "-i", asset[name], "-map", "0:v:0", "-map", "0:a:0",
                       "-c:v", "copy", "-af", f"aresample=48000:first_pts=0,volume={gain}dB", "-c:a", "aac", "-b:a", "160k",
                       "-movflags", "+faststart", str(partial)])
                _save_stage(stage, stage_key, {"sha256": fingerprint(partial)})
                partial.replace(target)
            outputs[name] = str(target)
        details, info = _scan(Path(outputs["path"])), probe(Path(outputs["path"]))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        if ((video["width"], video["height"]) != (asset["width"], asset["height"])
                or abs(info["duration_seconds"]-asset["duration_seconds"]) > .3
                or video["codec_name"] != "h264" or audio["codec_name"] != "aac"
                or abs(float(video.get("duration", info["duration_seconds"]))-float(audio.get("duration", info["duration_seconds"]))) > .2):
            raise ValueError("La correction audio a changé la durée, les pistes ou les dimensions.")
        if any(fingerprint(Path(item["path"])) != item["sha256"] for item in paths.values()):
            raise ValueError("L'entrée audio a changé pendant la correction.")
        result = copy.deepcopy(asset)
        result.update(**outputs, asset_id="asset-"+key[:20], cache_key=key,
                      sha256=fingerprint(Path(outputs["path"])), master_sha256=fingerprint(Path(outputs["master_path"])),
                      duration_seconds=info["duration_seconds"], qa_status="needs_review",
                      audio_headroom={"version": HEADROOM_VERSION, "gain_db": gain, 'decoded_input_peaks_db': peaks,
                                      "original_asset_id": asset["asset_id"], "original_sha256": asset["sha256"],
                                      "video_stream": "copied_without_reencoding", "scope": "output_headroom_only_not_source_restoration"})
        result["parameters"] = {**asset.get("parameters", {}), "output_gain_db": gain, "audio_input_sha256": asset["sha256"]}
        result["qa"]["details"] = details
        result["qa"]["technical"] = "passed" if (not details["black_intervals_seconds"] and not details["silence_events"]
            and details["max_volume_db"] is not None and details["max_volume_db"] <= -.1) else "needs_review"
        result["qa"]["quality_revision_sha256"] = result["sha256"]
        result["frames"] = _frames(Path(result["path"]), directory, result["duration_seconds"])
        result["contact_sheet"] = str(directory / "contact-sheet.jpg")
        result.pop("local_quality", None)
        _save_stage(receipt, identity, result)
        return result
