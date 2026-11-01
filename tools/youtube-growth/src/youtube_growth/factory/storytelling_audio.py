"""Measured speech, separate sound stems and a conservative durable call ledger."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import wave

from .contracts import digest, iso, utcnow
from .elevenlabs import ElevenLabsClient, GenerationUnknown, ProviderError, parse_audio_response, composition_duration
from .local_lock import local_lock
from .media import fingerprint
from .narrative import SAPI_SCRIPT, audio_duration, join_waves, spoken
from .storytelling_contracts import sound_level_db

VERSION = 2


def _paid_enabled(config):
    options = config.get("storytelling", {})
    if options.get("paid_calls_enabled") is not True or options.get("elevenlabs", {}).get("enabled") is not True:
        raise ValueError("storytelling_paid_calls_disabled")


def _write(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def _number(value, code, low=0, high=float("inf")):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(code)
    return float(value)


def _cancelled(store, story_id):
    row = store.get("storytelling_control", story_id) or {}
    if row.get("status") in {"paused", "cancelled"}:
        raise ValueError("storytelling_" + row["status"])


def budget_status(store, story_id, budget):
    rows = [r for r in store.records("storytelling_audio_call") if r["story_id"] == story_id]
    charged = [r for r in rows if r["status"] in {"committed", "completed", "unknown", "confirmed"}]
    return {"currency": budget["currency"], "limit": budget["limit"],
            "estimated": sum(r["estimate"] for r in rows),
            "committed": sum(r.get("confirmed_amount", r["estimate"]) if r.get("confirmed_amount") is not None else r["estimate"] for r in charged),
            "confirmed": sum(r["confirmed_amount"] for r in rows if r.get("confirmed_amount") is not None),
            "confirmed_coverage": "partial" if any(r.get("confirmed_amount") is None for r in charged) else "complete",
            "unknown_calls": [r["call_id"] for r in rows if r["status"] in {"unknown", "committed"}], "calls": rows}


def reserve_cost(store, story_id, identity, budget, estimate):
    """Reserve under BEGIN IMMEDIATE; a second process cannot spend the same headroom."""
    limit = _number(budget.get("limit"), "storytelling_budget_invalid")
    estimate = _number(estimate, "storytelling_estimate_invalid")
    currency = budget.get("currency")
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("storytelling_budget_invalid")
    # The resource cache is shared across projects. Its uncertain generation must
    # also be shared, otherwise a new story_id could trigger the same paid POST.
    call_id = digest({"provider": "elevenlabs", "identity": identity})
    with store.transaction():
        previous = store.get("storytelling_audio_call", call_id)
        if previous:
            return previous, False
        if identity.get("logical_resource") and any(
                r.get("logical_resource") == identity["logical_resource"] and r["status"] in {"committed", "unknown"}
                for r in store.records("storytelling_audio_call")):
            raise ValueError("storytelling_generation_unknown_reconcile_required")
        rows = [r for r in store.records("storytelling_audio_call") if r["story_id"] == story_id and r["status"] in {"committed", "completed", "unknown", "confirmed"}]
        if any(r["currency"] != currency for r in rows):
            raise ValueError("storytelling_budget_currency_changed")
        total = sum(r["confirmed_amount"] if r.get("confirmed_amount") is not None else r["estimate"] for r in rows)
        if estimate <= 0 or total + estimate > limit + 1e-9:
            raise ValueError("storytelling_budget_exceeded")
        row = {"call_id": call_id, "story_id": story_id, "identity": digest(identity), "currency": currency,
               "estimate": estimate, "confirmed_amount": None, "status": "committed", "operation_kind": identity.get("kind"),
               "logical_resource": identity.get("logical_resource"), "created_at": iso(utcnow())}
        store.put("storytelling_audio_call", call_id, row)
    return row, True


def _update_call(store, row, **updates):
    row = {**row, **updates, "updated_at": iso(utcnow())}
    store.put("storytelling_audio_call", row["call_id"], row)
    return row


def _paid_audio(store, config, script, identity, directory, estimate, callback):
    _paid_enabled(config)
    # One generation per account on this host. A busy lock creates no reservation.
    with local_lock(store.directory / "storytelling-provider-locks" / "elevenlabs"):
        return _paid_audio_locked(store, config, script, identity, directory, estimate, callback)


def _paid_audio_locked(store, config, script, identity, directory, estimate, callback):
    _paid_enabled(config)
    settings = config.get("storytelling", {})
    budget = script.get("budget")
    if not isinstance(budget, dict):
        raise ValueError("storytelling_budget_required")
    rate_currency = settings.get("elevenlabs", {}).get("currency")
    if rate_currency != budget.get("currency"):
        raise ValueError("storytelling_rate_currency_mismatch")
    _cancelled(store, script["story_id"])
    row, is_new = reserve_cost(store, script["story_id"], identity, budget, estimate)
    raw = directory / "response.bin"
    headers_path = directory / "response-headers.json"
    if not is_new:
        if raw.exists() and headers_path.exists():
            if (not row.get("response_sha256") or not row.get("headers_sha256")
                    or fingerprint(raw) != row["response_sha256"] or fingerprint(headers_path) != row["headers_sha256"]):
                raise ValueError("storytelling_provider_response_changed")
            headers = json.loads(headers_path.read_text(encoding="utf-8"))
            return raw.read_bytes(), headers, row
        if row["status"] in {"committed", "unknown", "completed", "confirmed"}:
            raise ValueError("storytelling_generation_unknown_reconcile_required")
        raise ValueError("storytelling_generation_rejected_correct_request")
    try:
        body, headers = callback()
        # Persist bytes before parsing/decoding; never depend on provider history.
        raw.write_bytes(body)
        headers = {k.lower(): v for k, v in headers.items() if k.lower() in {"content-type", "request-id", "history-item-id", "song-id", "character-cost"}}
        _write(headers_path, headers)
        _update_call(store, row, status="completed", response_sha256=fingerprint(raw), headers_sha256=fingerprint(headers_path),
                     response_directory=str(directory.resolve()), request_id=headers.get("request-id"))
        return body, headers, row
    except GenerationUnknown:
        _update_call(store, row, status="unknown")
        raise ValueError("storytelling_generation_unknown_reconcile_required") from None
    except ProviderError:
        _update_call(store, row, status="rejected")
        raise
    except BaseException:
        _update_call(store, row, status="unknown")
        raise


def _run_ffmpeg(arguments):
    executable = shutil.which("ffmpeg")
    if not executable:
        raise ValueError("ffmpeg_missing")
    process = subprocess.run([executable, "-hide_banner", "-loglevel", "error", "-nostdin", *arguments], capture_output=True, timeout=600)
    if process.returncode:
        raise ValueError("storytelling_audio_conversion_failed")


def _normalize(source, target):
    if source.resolve() == target.resolve():
        raise ValueError("storytelling_audio_source_overwrite")
    _run_ffmpeg(["-y", "-i", str(source), "-vn", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(target)])


def _load_cached(path, identity):
    if not path.exists():
        return None
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("identity") != identity:
        raise ValueError("storytelling_audio_cache_mismatch")
    for item in row["result"].get("artifacts", []):
        p = Path(item["path"])
        if not p.is_file() or fingerprint(p) != item["sha256"]:
            raise ValueError("storytelling_audio_cache_changed")
    return row["result"]


def _save_cache(path, identity, result):
    _write(path, {"identity": identity, "result": result})
    return result


def _artifact(path):
    return {"path": str(path), "sha256": fingerprint(path)}


def _validate_alignment(alignment, duration):
    names = ("characters", "character_start_times_seconds", "character_end_times_seconds")
    if any(not isinstance(alignment.get(name), list) for name in names):
        raise ValueError("elevenlabs_alignment_invalid")
    chars, starts, ends = (alignment[name] for name in names)
    if not chars or not len(chars) == len(starts) == len(ends):
        raise ValueError("elevenlabs_alignment_invalid")
    if any(not isinstance(character, str) for character in chars):
        raise ValueError("elevenlabs_alignment_invalid")
    last = 0.
    for start, end in zip(starts, ends):
        _number(start, "elevenlabs_alignment_invalid", 0, duration + .1)
        _number(end, "elevenlabs_alignment_invalid", start, duration + .1)
        if start < last:
            raise ValueError("elevenlabs_alignment_invalid")
        last = start


def estimate_audio(script, config):
    """Configured upper bounds, never pretend they are a provider invoice."""
    options = config.get("storytelling", {}).get("elevenlabs", {})
    speech, music, effects = 0, 0., 0.
    for scene in script.get("scenes", []):
        for line in scene.get("utterances", []):
            voice = script["speakers"][line["speaker_id"]]["voice"]
            if voice.get("provider") == "elevenlabs":
                speech += len(spoken(line["text"], voice.get("pronunciations", {})))
        sound = scene.get("sound", {})
        if isinstance(sound.get("music"), dict) and sound["music"].get("provider", "elevenlabs") == "elevenlabs":
            music += _music_duration(sound["music"])
        effects += sum(_number(s.get("duration_seconds"), "storytelling_sound_duration_required", .5, 30) for s in sound.get("effects", []) if s.get("provider", "elevenlabs") == "elevenlabs")
    amounts = []
    for units, key in ((speech, "cost_per_character_upper_bound"), (music, "cost_per_music_second_upper_bound"), (effects, "cost_per_effect_second_upper_bound")):
        if units:
            amounts.append(units * _number(options.get(key), "elevenlabs_rate_required"))
    return {"amount_upper_bound": sum(amounts), "currency": options.get("currency", script.get("budget", {}).get("currency")),
            "speech_characters": speech, "music_seconds": music, "effect_seconds": effects,
            "basis": "configured_upper_bounds_before_cache", "confirmed_amount": None}


def _music_duration(spec):
    plan = spec.get("composition_plan")
    prompt = spec.get("prompt")
    if bool(plan) == bool(prompt):
        raise ValueError("music_prompt_or_plan_required")
    if plan:
        duration = composition_duration(plan)
        if spec.get("duration_seconds") is not None and abs(_number(spec["duration_seconds"], "storytelling_music_duration_invalid") - duration) > .001:
            raise ValueError("storytelling_music_plan_duration_mismatch")
        return duration
    return _number(spec.get("duration_seconds"), "storytelling_sound_duration_required", 3, 600)


def split_text(text, limit):
    """Sentence/word boundaries only; reject a single token exceeding the API limit."""
    if not isinstance(text, str) or not text.strip() or limit < 1:
        raise ValueError("storytelling_speech_text_invalid")
    words = text.split()
    chunks, current = [], ""
    for word in words:
        if len(word) > limit:
            raise ValueError("storytelling_speech_word_too_long")
        candidate = (current + " " + word).strip()
        if len(candidate) > limit:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def caption_chunks(text, limit=150):
    """Speech-sized caption text; timing will be measured from each actual file."""
    result = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        result.extend(split_text(sentence, limit))
    return result


def _system(text, voice, directory):
    if os.name != "nt" or not shutil.which("powershell.exe"):
        raise ValueError("system_voice_unavailable")
    name = voice.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("system_voice_name_required")
    script_path = directory / "speak.ps1"
    script_path.write_text(SAPI_SCRIPT, encoding="utf-8-sig")
    raw = directory / "system.wav"
    request_path = directory / "speech-request.json"
    rate = _number(voice.get("rate", 0), "system_voice_rate_invalid", -5, 5)
    _write(request_path, {"voice": name, "rate": rate, "items": [{"text": text, "path": str(raw)}]})
    process = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(script_path), "-Request", str(request_path)], capture_output=True, timeout=900)
    if process.returncode:
        raise ValueError("system_voice_unavailable")
    return raw


def _voicestudio(store, config, script, text, voice, directory, target):
    """One local take per caption sentence, joined with a measured breathing pause."""
    from .voicestudio import DEFAULT_URL, VoiceStudio, live_voice, request_fields
    options = config.get("voicestudio", {})
    client = VoiceStudio(options.get("base_url", DEFAULT_URL), timeout=options.get("timeout_seconds", 1800))
    pause = voice["settings"].get("pause_between_sentences_seconds", .3)
    # One GPU service per host: takes are serialized like paid provider calls.
    with local_lock(store.directory / "storytelling-provider-locks" / "voicestudio"):
        live = live_voice(client, voice)
        chunks, paths, captions, offset = caption_chunks(text), [], [], 0.
        for index, caption in enumerate(chunks):
            _cancelled(store, script["story_id"])
            chunk_dir = directory / ("sentence-" + str(index))
            chunk_dir.mkdir(exist_ok=True)
            raw = chunk_dir / "voicestudio.wav"
            if not raw.exists():
                temporary = raw.with_suffix(".part")
                temporary.write_bytes(client.generate(request_fields(voice, spoken(caption, voice.get("pronunciations", {})))))
                temporary.replace(raw)
            wav = chunk_dir / "normalized.wav"
            _normalize(raw, wav)
            duration = audio_duration(wav)
            if duration <= .05:
                raise ValueError("storytelling_speech_empty")
            captions.append({"text": caption, "start_seconds": offset, "end_seconds": offset + duration})
            offset += duration + pause
            paths.append(wav)
        join_waves(paths, target, pause=pause)
    sent = {k: v for k, v in request_fields(voice, "").items() if k != "text"}
    return captions, {"profile_id": voice["profile_id"], "profile_name": live["profile_name"], "consent": live["consent"],
                      "engine": voice["engine"], "voicestudio_version": live["version"], "request": sent,
                      "sentences": len(chunks), "pause_between_sentences_seconds": pause}


def _utterance(store, config, script, utterance, voice, cache, *, client=None):
    if not voice.get("authorization"):
        raise ValueError("storytelling_voice_authorization_required")
    text = utterance["text"]
    spoken_text = spoken(text, voice.get("pronunciations", {}))
    provider = voice.get("provider", "system")
    if provider not in {"system", "recordings", "elevenlabs", "voicestudio"}:
        raise ValueError("storytelling_voice_provider_unavailable")
    source = None
    source_sha256 = None
    recording_captions = None
    if provider == "recordings":
        recording = utterance.get("recording") or voice.get("recordings", {}).get(utterance["utterance_id"])
        if not isinstance(recording, dict) or not recording.get("sha256"):
            raise ValueError("storytelling_recording_required")
        source = Path(recording["path"]).resolve(strict=True)
        source_sha256 = fingerprint(source)
        if source_sha256 != recording["sha256"]:
            raise ValueError("storytelling_recording_changed")
        recording_captions = recording.get("caption_segments")
    # Delivery descriptions remain metadata. Only supported numerical settings enter API requests.
    settings = dict(voice.get("settings", {}))
    delivery = utterance.get("delivery", {})
    if "speed" in delivery:
        settings["speed"] = _number(delivery["speed"], "storytelling_speed_invalid", .7, 1.2)
    voice_identity = {key: value for key, value in voice.items() if key != "recordings"}
    generation_version = utterance.get("generation_version", 1)
    if type(generation_version) is not int or generation_version < 1:
        raise ValueError("storytelling_generation_version_invalid")
    identity = {"version": VERSION, "text": spoken_text, "caption": text, "voice": voice_identity,
                "provider": provider, "settings": settings, "source_sha256": source_sha256,
                "recording_caption_segments": recording_captions, "generation_version": generation_version}
    key = digest(identity)
    directory = cache / key
    directory.mkdir(parents=True, exist_ok=True)
    with local_lock(directory):
        receipt = directory / "receipt.json"
        previous = _load_cached(receipt, key)
        if previous:
            return previous
        target = directory / "speech.wav"
        alignment, metadata, captions = None, {}, None
        if provider == "system":
            chunks, paths, captions, offset = caption_chunks(text), [], [], 0.
            for index, caption in enumerate(chunks):
                _cancelled(store, script["story_id"])
                chunk_dir = directory / ("sentence-" + str(index))
                chunk_dir.mkdir(exist_ok=True)
                wav = chunk_dir / "normalized.wav"
                _normalize(_system(spoken(caption, voice.get("pronunciations", {})), voice, chunk_dir), wav)
                duration = audio_duration(wav)
                if duration <= .05:
                    raise ValueError("storytelling_speech_empty")
                captions.append({"text": caption, "start_seconds": offset, "end_seconds": offset + duration})
                offset += duration
                paths.append(wav)
            join_waves(paths, target, pause=0)
            metadata = {"measured_caption_chunks": len(chunks)}
        elif provider == "voicestudio":
            captions, metadata = _voicestudio(store, config, script, text, {**voice, "settings": settings}, directory, target)
        elif provider == "recordings":
            _normalize(source, target)
            if recording_captions is not None:
                if not isinstance(recording_captions, list) or not recording_captions:
                    raise ValueError("storytelling_recording_captions_invalid")
                captions, last, duration = [], 0., audio_duration(target)
                for segment in recording_captions:
                    if not isinstance(segment, dict) or not isinstance(segment.get("text"), str) or not segment["text"].strip():
                        raise ValueError("storytelling_recording_captions_invalid")
                    start = _number(segment.get("start_seconds"), "storytelling_recording_captions_invalid", last, duration + .01)
                    end = _number(segment.get("end_seconds"), "storytelling_recording_captions_invalid", start, duration + .01)
                    if end <= start:
                        raise ValueError("storytelling_recording_captions_invalid")
                    captions.append({"text": segment["text"], "start_seconds": start, "end_seconds": end})
                    last = end
                if " ".join(" ".join(c["text"].split()) for c in captions) != " ".join(text.split()):
                    raise ValueError("storytelling_recording_caption_coverage_invalid")
        else:
            _paid_enabled(config)
            client = client or ElevenLabsClient(config.get("storytelling", {}).get("elevenlabs", {}))
            model_id = voice.get("model_id")
            if not model_id:
                raise ValueError("elevenlabs_model_required")
            _, limit = client.validate_voice(voice.get("voice_id"), model_id)
            chunks = split_text(spoken_text, min(limit, 4000))
            parts, alignment_rows, local = [], [], 0.
            for index, chunk in enumerate(chunks):
                part_dir = directory / str(index)
                part_dir.mkdir(exist_ok=True)
                operation = {"kind": "tts", "resource": key, "part": index, "text": chunk,
                             "logical_resource": digest({"identity": {k: v for k, v in identity.items() if k != "generation_version"}, "part": index})}
                per_character = config.get("storytelling", {}).get("elevenlabs", {}).get("cost_per_character_upper_bound")
                estimate = len(chunk) * _number(per_character, "elevenlabs_tts_rate_required")
                body, headers, _ = _paid_audio(store, config, script, operation, part_dir, estimate,
                    lambda: client.tts(chunk, voice["voice_id"], model_id, voice_settings=settings,
                                       previous_text=chunks[index-1] if index else None,
                                       next_text=chunks[index+1] if index+1 < len(chunks) else None,
                                       pronunciation_dictionary_locators=voice.get("pronunciation_dictionary_locators")))
                data, details = parse_audio_response(body, headers.get("content-type", "application/json"))
                compressed = part_dir / "audio.mp3"
                compressed.write_bytes(data)
                _write(part_dir / "provider.json", details)
                wav = part_dir / "audio.wav"
                _normalize(compressed, wav)
                length = audio_duration(wav)
                raw_alignment = details.get("alignment")
                if not raw_alignment:
                    raise ValueError("elevenlabs_alignment_coverage_unverified")
                _validate_alignment(raw_alignment, length)
                if " ".join("".join(raw_alignment["characters"]).split()) != " ".join(chunk.split()):
                    raise ValueError("elevenlabs_alignment_text_coverage_mismatch")
                align = details.get("normalized_alignment") or raw_alignment
                if align:
                    _validate_alignment(align, length)
                    alignment_rows.append({"offset_seconds": local, "alignment": align})
                local += length
                parts.append(wav)
            join_waves(parts, target, pause=0)
            alignment = alignment_rows or None
            metadata = {"model_id": model_id, "voice_id": voice["voice_id"], "parts": len(parts), "output_format": "mp3_44100_128"}
        duration = audio_duration(target)
        if duration <= .05:
            raise ValueError("storytelling_speech_empty")
        result = {**_artifact(target), "duration_seconds": duration, "alignment": alignment,
                  "alignment_kind": "provider_characters" if alignment else "measured_caption_chunks" if captions else "measured_utterance_boundaries",
                  "provider": provider, "provider_metadata": metadata, "spoken_text": spoken_text, "caption_segments": captions,
                  "artifacts": [_artifact(target)]}
        return _save_cache(receipt, key, result)


# Placement and volume belong to the mix, not to the generated or imported resource.
MIX_FIELDS = {"offset_seconds", "gain_db", "level_db", "fade_in_seconds", "fade_out_seconds", "purpose", "utterance_id", "sound_id"}
# Before level_db was applied, it still entered the key; such caches remain reusable.
LEGACY_MIX_FIELDS = MIX_FIELDS - {"level_db"}


def _sound_identity(spec, kind, cache):
    def identity(excluded):
        return {"version": VERSION, "kind": kind, "spec": {k: v for k, v in spec.items() if k not in excluded}}
    current = identity(MIX_FIELDS)
    if "level_db" in spec:
        legacy = identity(LEGACY_MIX_FIELDS)
        # A started legacy resource keeps its key: no second paid call or new render for it.
        if (cache / digest(legacy)).is_dir():
            return legacy
    return current


def _sound(store, config, script, spec, kind, cache, *, client=None):
    identity = _sound_identity(spec, kind, cache)
    generation_spec = identity["spec"]
    key = digest(identity)
    directory = cache / key
    directory.mkdir(parents=True, exist_ok=True)
    with local_lock(directory):
        previous = _load_cached(directory / "receipt.json", key)
        if previous:
            return previous
        provider = spec.get("provider", "elevenlabs")
        target = directory / "sound.wav"
        if provider == "recordings":
            if not isinstance(spec.get("path"), str) or not spec.get("sha256"):
                raise ValueError("storytelling_sound_source_unverified")
            source = Path(spec["path"]).resolve(strict=True)
            authorization = spec.get("authorization")
            if (not isinstance(authorization, str) or not authorization.strip() or authorization.strip() == "usage_to_confirm"
                    or fingerprint(source) != spec["sha256"]):
                raise ValueError("storytelling_sound_source_unverified")
            _normalize(source, target)
        elif provider == "elevenlabs":
            _paid_enabled(config)
            options = config.get("storytelling", {}).get("elevenlabs", {})
            client = client or ElevenLabsClient(options)
            length = _music_duration(spec) if kind == "music" else _number(spec.get("duration_seconds"), "storytelling_sound_duration_required", .5, 30)
            rate = _number(options.get("cost_per_music_second_upper_bound" if kind == "music" else "cost_per_effect_second_upper_bound"), "elevenlabs_sound_rate_required")
            if kind == "music":
                if not options.get("music_enabled"):
                    raise ValueError("elevenlabs_music_not_enabled")
                callback = lambda: client.music(model_id=spec.get("model_id", options.get("music_model_id", "music_v1")),
                    prompt=spec.get("prompt"), duration_seconds=length if not spec.get("composition_plan") else None,
                    composition_plan=spec.get("composition_plan"))
            else:
                if not options.get("effects_enabled"):
                    raise ValueError("elevenlabs_effects_not_enabled")
                callback = lambda: client.sound_effect(spec["prompt"], length, loop=spec.get("loop", False), model_id=spec.get("model_id", "eleven_text_to_sound_v2"))
            operation = {**identity, "logical_resource": digest({"kind": kind, "spec": {k: v for k, v in generation_spec.items() if k != "generation_version"}})}
            body, headers, _ = _paid_audio(store, config, script, operation, directory, length * rate, callback)
            data, details = parse_audio_response(body, headers.get("content-type", "audio/mpeg"))
            compressed = directory / "audio.mp3"
            compressed.write_bytes(data)
            _write(directory / "provider.json", details)
            _normalize(compressed, target)
        else:
            raise ValueError("storytelling_sound_provider_unavailable")
        result = {**_artifact(target), "duration_seconds": audio_duration(target), "provider": provider, "kind": kind,
                  "artifacts": [_artifact(target)]}
        return _save_cache(directory / "receipt.json", key, result)


def produce_audio(store, config, script, directory: Path, *, synthetic=False):
    """Real waveform lengths become the timeline; estimated text duration never does."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cache = store.directory / "storytelling-cache" / "audio"
    cache.mkdir(parents=True, exist_ok=True)
    cursor, scenes, artifacts, sound_tracks = 0., [], [], []
    for scene in script["scenes"]:
        _cancelled(store, script["story_id"])
        rows, paths, pauses = [], [], []
        scene_start = cursor
        for utterance in scene["utterances"]:
            _cancelled(store, script["story_id"])
            voice = script["speakers"][utterance["speaker_id"]]["voice"]
            item = _utterance(store, config, script, utterance, voice, cache)
            duration = item["duration_seconds"]
            # A pause written in the script is silence after the measured take; the voice itself is never stretched.
            pause = _number((utterance.get("delivery") or {}).get("pause_after_seconds", 0), "storytelling_pause_invalid", 0, 10)
            rows.append({**item, "utterance_id": utterance["utterance_id"], "speaker_id": utterance["speaker_id"], "text": utterance["text"],
                         "start_seconds": cursor, "end_seconds": cursor + duration, **({"pause_after_seconds": pause} if pause else {})})
            paths.append(Path(item["path"]))
            pauses.append(pause)
            artifacts.extend(item["artifacts"])
            cursor += duration + pause
        if not paths:
            raise ValueError("storytelling_scene_speech_missing")
        scene_identity = digest({"paths": [_artifact(p) for p in paths], **({"pauses": pauses} if any(pauses) else {})})
        target = directory / (scene_identity + ".wav")
        scene_receipt = target.with_suffix(".receipt.json")
        if target.exists():
            if not scene_receipt.exists() or json.loads(scene_receipt.read_text(encoding="utf-8")).get("sha256") != fingerprint(target):
                raise ValueError("storytelling_scene_audio_changed")
        else:
            join_waves(paths, target, pauses=pauses)
            _write(scene_receipt, _artifact(target))
        measured = audio_duration(target)
        scenes.append({"scene_id": scene["scene_id"], "start_seconds": scene_start, "duration_seconds": measured,
                       **_artifact(target), "utterances": rows})
        artifacts.append(_artifact(target))
        sound = scene.get("sound", {})
        specifications = ([('music', sound["music"])] if isinstance(sound.get("music"), dict) else []) + [("effect", s) for s in sound.get("effects", [])]
        for kind, spec in specifications:
            _cancelled(store, script["story_id"])
            # Mix values are checked before any import or paid generation.
            offset = _number(spec.get("offset_seconds", 0), "storytelling_sound_offset_invalid", 0, measured)
            gain = sound_level_db(spec, kind)
            stem = _sound(store, config, script, spec, kind, cache)
            sound_tracks.append({**stem, "scene_id": scene["scene_id"], "start_seconds": scene_start + offset,
                                 "duration_seconds": min(stem["duration_seconds"], measured - offset), "gain_db": gain,
                                 "fade_in_seconds": min(.4, measured/4), "fade_out_seconds": min(.6, measured/4)})
            artifacts.extend(stem["artifacts"])
    provider_validation = "local_or_imported_only" if not any(u["provider"] == "elevenlabs" for s in scenes for u in s["utterances"]) else "elevenlabs_responses_received"
    result = {"version": VERSION, "scenes": scenes, "duration_seconds": cursor, "sound_tracks": sound_tracks,
              "artifacts": artifacts, "synthetic": synthetic, "provider_validation": provider_validation,
              "mix_status": "separate_stems_ready", "listening_review": "pending"}
    _write(directory / "audio.json", result)
    return result
