"""Compare exported picture and sound with the actual source at every edit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .shorts import _require_media_tools, _sha256
from .storage import save_json


def media_bytes(ffmpeg: str, path: Path, time: float, audio: bool, duration: float = 2) -> bytes:
    command = [ffmpeg, "-nostdin", "-v", "error", "-ss", f"{time:.6f}", "-i", str(path)]
    command += (["-t", str(duration), "-vn", "-ac", "1", "-ar", "4000", "-f", "f32le", "-"] if audio else
                ["-frames:v", "1", "-vf", "scale=128:72,format=gray", "-f", "rawvideo", "-"])
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("Échec du décodage pour la comparaison des médias.")
    return result.stdout


def correlation(reference, sample):
    import numpy as np
    a, b = reference.astype(np.float64), sample.astype(np.float64)
    a, b = a-a.mean(), b-b.mean()
    denominator = np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a, b)/denominator) if denominator > 1e-12 else None


def compare(source: Path, video: Path, timeline: list[dict], ffmpeg: str) -> dict:
    import numpy as np
    checks = []
    for index, edit in enumerate(timeline):
        length = edit["output_end"] - edit["output_start"]
        if length < 1:
            checks.append({"edit": index, "status": "too_short_for_correlation"})
            continue
        window = min(2, length-.4)
        for ratio in (.15, .5, .85):
            offset = max(.15, min(length-window-.15, (length-window)*ratio))
            source_time, output_time = edit["source_start"]+offset, edit["output_start"]+offset
            a = np.frombuffer(media_bytes(ffmpeg, source, source_time, True, window), dtype="<f4")
            margin = .08
            b = np.frombuffer(media_bytes(ffmpeg, video, output_time-margin, True, window+2*margin), dtype="<f4")
            scores = [(correlation(a, b[start:start+len(a)]), start) for start in range(0, len(b)-len(a)+1, 4)]
            available = [(value, lag) for value, lag in scores if value is not None]
            if available:
                audio_score, lag = max(available)
                lag_ms = (lag/4000-margin)*1000
            else:
                audio_score, lag_ms = None, None
            picture_a = np.frombuffer(media_bytes(ffmpeg, source, source_time, False), dtype=np.uint8)
            picture_b = np.frombuffer(media_bytes(ffmpeg, video, output_time, False), dtype=np.uint8)
            picture_score = correlation(picture_a, picture_b) if len(picture_a) == len(picture_b) and len(picture_a) else None
            # Silent pauses are explicit, never reported as matching speech.
            passed = audio_score is not None and audio_score >= .94 and abs(lag_ms) <= 25 and picture_score is not None and picture_score >= .94
            checks.append({"edit": index, "position": ratio, "source_time": round(source_time, 3), "output_time": round(output_time, 3),
                           "audio_correlation": None if audio_score is None else round(audio_score, 5), "audio_lag_ms": lag_ms,
                           "picture_correlation": None if picture_score is None else round(picture_score, 5), "passed": passed})
    return {"status": "source_correspondence_verified" if checks and all(c.get("passed") for c in checks) else "needs_review",
            "checks": checks, "full_listening": False, "semantic_review": "required_before_publication"}


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.output.resolve(strict=True)
    manifest = json.loads((root / "thematic-manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest["source"])
    if _sha256(source) != manifest["options"]["source_sha256"]:
        raise ValueError("La source a changé depuis le rendu.")
    ffmpeg, _ = _require_media_tools()
    result = []
    for row in manifest["videos"]:
        directory = (root / row["folder"]).resolve()
        if not directory.is_relative_to(root):
            raise ValueError("Vidéo hors du dossier autorisé.")
        video = directory / "video.mp4"
        if _sha256(video) != row["technical"]["sha256"]:
            raise ValueError("La vidéo a changé depuis son décodage.")
        timeline = json.loads((directory / "montage.json").read_text(encoding="utf-8"))["timeline"]
        checked = {"folder": row["folder"], "video_sha256": _sha256(video), **compare(source, video, timeline, ffmpeg)}
        save_json(directory / "correspondance-source.json", checked)
        print(f"{row['folder']} : {checked['status']} ({len(checked['checks'])} mesures)", flush=True)
        result.append(checked)
    summary = {"status": "source_correspondence_verified" if result and all(r["status"] == "source_correspondence_verified" for r in result) else "needs_review",
               "videos": result, "full_listening": False}
    save_json(root / "correspondance-source.json", summary)
    return {"status": summary["status"], "videos": len(result)}


if __name__ == "__main__":
    try:
        result = main()
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "source_correspondence_verified" else 2)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
