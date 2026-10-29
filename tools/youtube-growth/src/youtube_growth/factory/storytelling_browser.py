"""Durable handoff to ElevenLabs in an authenticated, visible browser session.

This module records work and imports results. It does not drive a browser or make
provider requests; a Codex session performs those actions through computer use.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

from .contracts import digest, iso, utcnow
from .media import fingerprint

KIND = "storytelling_browser_request"


def _integer(value, field):
    if type(value) is not int or value < 0:
        raise ValueError("storytelling_browser_" + field + "_required")
    return value


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("storytelling_browser_" + field + "_required")
    return value.strip()


def _artifact(path):
    return {"path": str(Path(path).resolve()), "sha256": fingerprint(Path(path))}


def _checked(row):
    if not Path(row["path"]).is_file() or fingerprint(Path(row["path"])) != row["sha256"]:
        raise ValueError("storytelling_browser_result_changed")


def _duration(path):
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as stream:
                value = stream.getnframes() / stream.getframerate()
        except (wave.Error, EOFError):
            raise ValueError("storytelling_browser_invalid_audio") from None
    else:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise ValueError("storytelling_browser_ffprobe_required")
        result = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                                capture_output=True, timeout=30, shell=False)
        if result.returncode:
            raise ValueError("storytelling_browser_invalid_audio")
        try:
            data = json.loads(result.stdout)
            if not any(s.get("codec_type") == "audio" for s in data.get("streams", [])):
                raise ValueError("storytelling_browser_invalid_audio")
            value = float(data.get("format", {}).get("duration", 0))
        except (ValueError, TypeError, KeyError):
            raise ValueError("storytelling_browser_invalid_audio") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError("storytelling_browser_invalid_audio")
    return value


def _assemble(parts, directory):
    """Measure downloaded chunks after PCM conversion, then join without padding."""
    from .local_lock import local_lock
    from .narrative import audio_duration, join_waves
    from .storytelling_audio import _normalize
    identity = {"version": 1, "parts": [{"result": row["result"], "text": row["spec"]["text"]} for row in parts]}
    output = Path(directory) / "assembled" / digest(identity)
    with local_lock(output):
        receipt = output / "assembly.json"
        if receipt.exists():
            value = json.loads(receipt.read_text(encoding="utf-8"))
            if value.get("identity") != identity:
                raise ValueError("storytelling_browser_assembly_changed")
            for artifact in value["artifacts"]:
                _checked(artifact)
            return value
        waves, segments, artifacts, cursor = [], [], [], 0.
        for index, row in enumerate(parts):
            _checked(row["result"])
            path = output / (str(index) + ".wav")
            _normalize(Path(row["result"]["path"]), path)
            length = audio_duration(path)
            segments.append({"text": row["spec"]["text"], "start_seconds": cursor, "end_seconds": cursor + length})
            cursor += length
            waves.append(path)
            artifacts.append(_artifact(path))
        target = output / "speech.wav"
        join_waves(waves, target, pause=0)
        artifacts.append(_artifact(target))
        value = {"identity": identity, "recording": {**_artifact(target), "caption_segments": segments}, "artifacts": artifacts}
        receipt.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return value


def prepare(store, script, directory):
    """Export requests and resolve only hash-checked completed results as recordings."""
    value = deepcopy(script)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    story_id = _text(value.get("story_id"), "story_id")
    credit_limit = value.get("budget", {}).get("browser_credit_limit")
    if credit_limit is not None:
        _integer(credit_limit, "credit_limit")
    requests, artifacts, pending = [], [], []

    def request(kind, anchor, spec):
        key = digest({"version": 1, "story_id": story_id, "kind": kind, "anchor": anchor, "spec": spec})
        row = store.get(KIND, key)
        if row is None:
            path = directory / key / "request.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"request_id": key, "story_id": story_id, "kind": kind, "anchor": anchor,
                       "spec": spec, "execution": "authenticated_elevenlabs_browser_in_codex_session",
                       "notice": "Texte oral séparé des intentions ; ne rien soumettre sans réservation de crédits."}
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            row = {**payload, "status": "waiting", "directory": str(path.parent), "request_file": _artifact(path),
                   "authorized_credit_limit": credit_limit,
                   "created_at": iso(utcnow())}
            with store.transaction():
                previous = store.get(KIND, key)
                if previous is None:
                    store.put(KIND, key, row)
                else:
                    row = previous
        if row["status"] == "waiting" and row.get("authorized_credit_limit") != credit_limit:
            row["authorized_credit_limit"] = credit_limit
            store.put(KIND, key, row)
        _checked(row["request_file"])
        artifacts.append(row["request_file"])
        if row["status"] == "completed":
            _checked(row["result"])
            artifacts.append(row["result"])
        else:
            pending.append(key)
        requests.append(row)
        return row

    for speaker_id, speaker in value.get("speakers", {}).items():
        voice = speaker.get("voice", {})
        if voice.get("provider") != "elevenlabs_browser":
            continue
        recordings = {}
        speaker_ready = True
        for scene in value.get("scenes", []):
            for utterance in scene.get("utterances", []):
                if utterance.get("speaker_id") != speaker_id:
                    continue
                oral = _text(utterance.get("text"), "spoken_text")
                from .storytelling_audio import split_text
                parts = []
                for index, text in enumerate(split_text(oral, 250)):
                    parts.append(request("speech", utterance["utterance_id"] + "-part" + str(index), {"text": text,
                        "utterance_id": utterance["utterance_id"], "speaker_id": speaker_id, "part_index": index,
                        "voice": {k: v for k, v in voice.items() if k not in {"provider", "authorization", "recordings"}},
                        "delivery": utterance.get("delivery", {}), "generation_version": utterance.get("generation_version", 1)}))
                if all(row["status"] == "completed" for row in parts):
                    assembled = _assemble(parts, directory)
                    recordings[utterance["utterance_id"]] = assembled["recording"]
                    artifacts.extend(assembled["artifacts"])
                else:
                    speaker_ready = False
        if speaker_ready:
            speaker["voice"] = {"provider": "recordings", "authorization": voice.get("authorization", "Voix autorisée du compte ElevenLabs via navigateur."),
                                "recordings": recordings, "origin": "elevenlabs_browser"}
    for scene in value.get("scenes", []):
        sound = scene.get("sound", {})
        cues = ([('music', sound['music'])] if sound.get("music") else [])
        cues += [("effect", cue) for cue in sound.get("effects", [])]
        for index, (kind, cue) in enumerate(cues):
            if cue.get("provider") != "elevenlabs_browser":
                continue
            spec = {k: v for k, v in cue.items() if k not in {"provider", "authorization", "source_id", "path", "sha256"}}
            _text(spec.get("prompt"), "sound_prompt")
            row = request(kind, scene["scene_id"] + ":" + str(index), spec)
            if row["status"] == "completed":
                cue.update(provider="recordings", path=row["result"]["path"], sha256=row["result"]["sha256"],
                           authorization=cue.get("authorization", "Audio du compte ElevenLabs via navigateur."))
    return {"ready": not pending, "script": value, "requests": requests, "artifacts": artifacts,
            "blocker": "storytelling_browser_session_required" if pending else None,
            "execution": "requires_active_codex_browser_session"}


def record_attempt(store, request_id, credit_limit, estimated_credits, evidence):
    """Reserve provider credits atomically before the user-interface submission."""
    limit = _integer(credit_limit, "credit_limit")
    estimate = _integer(estimated_credits, "estimated_credits")
    if estimate == 0:
        raise ValueError("storytelling_browser_positive_estimate_required")
    evidence = _text(evidence, "attempt_evidence")
    with store.transaction():
        row = store.get(KIND, request_id)
        if row is None:
            raise ValueError("storytelling_browser_request_missing")
        if row["status"] != "waiting":
            raise ValueError("storytelling_browser_reconcile_required")
        authorized = row.get("authorized_credit_limit")
        if authorized is None:
            raise ValueError("storytelling_browser_credit_limit_required")
        if limit > authorized:
            raise ValueError("storytelling_browser_credit_authorization_exceeded")
        if any(r["request_id"] != request_id and r["story_id"] == row["story_id"] and r["kind"] == row["kind"]
               and r["anchor"] == row["anchor"] and r["status"] in {"submitted", "unknown"} for r in store.records(KIND)):
            raise ValueError("storytelling_browser_reconcile_required")
        existing = [r for r in store.records(KIND) if r["story_id"] == row["story_id"] and r["status"] in {"submitted", "unknown", "completed"}]
        committed = sum(r.get("actual_credits") if r.get("actual_credits") is not None else r.get("estimated_credits", 0) for r in existing)
        if committed + estimate > limit:
            raise ValueError("storytelling_browser_credit_limit_exceeded")
        row.update(status="submitted", credit_limit=limit, estimated_credits=estimate, actual_credits=None,
                   attempt_evidence=evidence, submitted_at=iso(utcnow()))
        store.put(KIND, request_id, row)
        store.event("storytelling_browser_submitted", row["story_id"], {"request_id": request_id, "estimated_credits": estimate})
    return row


def mark_unknown(store, request_id, evidence):
    evidence = _text(evidence, "uncertainty_evidence")
    with store.transaction():
        row = store.get(KIND, request_id)
        if row is None or row["status"] not in {"submitted", "unknown"}:
            raise ValueError("storytelling_browser_submitted_request_required")
        row.update(status="unknown", uncertainty_evidence=evidence, uncertain_at=iso(utcnow()))
        store.put(KIND, request_id, row)
    return row


def complete_request(store, request_id, path, provenance, actual_credits=None):
    """Import a downloaded result with a durable link to its browser submission."""
    if actual_credits is not None:
        _integer(actual_credits, "actual_credits")
    if not isinstance(provenance, dict) or not provenance.get("evidence"):
        raise ValueError("storytelling_browser_provenance_required")
    allowed = {"provider", "surface", "voice_name", "voice_id", "model", "generated_at", "evidence", "rights", "resource_id"}
    if set(provenance) - allowed or any(not isinstance(v, str) for v in provenance.values()):
        raise ValueError("storytelling_browser_provenance_fields_invalid")
    source = Path(path).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"} or source.stat().st_size > 1_000_000_000:
        raise ValueError("storytelling_browser_audio_file_required")
    duration = _duration(source)
    sha = fingerprint(source)
    with store.transaction():
        row = store.get(KIND, request_id)
        if row is None:
            raise ValueError("storytelling_browser_request_missing")
        if row["kind"] == "speech":
            speaker_id = _text(row["spec"].get("speaker_id"), "speaker_id")
            name = _text(provenance.get("voice_name"), "voice_name")
            normalized = " ".join(name.split()).casefold()
            selection = row["spec"].get("voice", {})
            configured_name = " ".join(str(selection.get("name", "")).split()).casefold()
            placeholder = "voix choisie dans elevenlabs"
            if normalized == placeholder:
                raise ValueError("storytelling_browser_voice_name_required")
            if configured_name and configured_name != placeholder and configured_name != normalized:
                raise ValueError("storytelling_browser_configured_voice_mismatch")
            if selection.get("voice_id") and provenance.get("voice_id") != selection["voice_id"]:
                raise ValueError("storytelling_browser_configured_voice_mismatch")
            map_id = row["story_id"] + ":" + speaker_id
            mapping = store.get("storytelling_browser_voice", map_id)
            if mapping is not None and (" ".join(mapping["voice_name"].split()).casefold() != normalized
                    or mapping.get("voice_id") and provenance.get("voice_id") and mapping["voice_id"] != provenance["voice_id"]):
                raise ValueError("storytelling_browser_speaker_voice_mismatch")
            if row["status"] not in {"submitted", "unknown", "completed"}:
                raise ValueError("storytelling_browser_submitted_request_required")
            if mapping is None:
                mapping = {"story_id": row["story_id"], "speaker_id": speaker_id, "voice_name": name,
                           "established_by": request_id, "validation": "declared_browser_provenance_not_listening", "created_at": iso(utcnow())}
            if provenance.get("voice_id"):
                mapping["voice_id"] = provenance["voice_id"]
            store.put("storytelling_browser_voice", map_id, mapping)
        if row["status"] == "completed":
            _checked(row["result"])
            if row["result"]["sha256"] != sha:
                raise ValueError("storytelling_browser_completed_result_mismatch")
            if actual_credits is not None and row.get("actual_credits") is None:
                row.update(actual_credits=actual_credits, credit_observation="confirmed",
                           estimate_exceeded=actual_credits > row.get("estimated_credits", 0))
                store.put(KIND, request_id, row)
            elif actual_credits is not None and row.get("actual_credits") != actual_credits:
                raise ValueError("storytelling_browser_confirmed_credits_changed")
            return row
        if row["status"] not in {"submitted", "unknown"}:
            raise ValueError("storytelling_browser_submitted_request_required")
        target = Path(row["directory"]) / (sha + source.suffix.lower())
        if target.exists():
            if fingerprint(target) != sha:
                raise ValueError("storytelling_browser_result_changed")
        else:
            with source.open("rb") as incoming, target.open("xb") as output:
                shutil.copyfileobj(incoming, output)
        if fingerprint(target) != sha:
            raise ValueError("storytelling_browser_result_changed")
        row.update(status="completed", result=_artifact(target), duration_seconds=duration, provenance=provenance,
                   actual_credits=actual_credits, completed_at=iso(utcnow()),
                   credit_observation="confirmed" if actual_credits is not None else "unknown_actual",
                   estimate_exceeded=actual_credits is not None and actual_credits > row.get("estimated_credits", 0))
        store.put(KIND, request_id, row)
        store.event("storytelling_browser_completed", row["story_id"], {"request_id": request_id, "actual_credits": actual_credits})
    return row
