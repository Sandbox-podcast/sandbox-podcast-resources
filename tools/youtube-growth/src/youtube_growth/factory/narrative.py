"""Resumable original productions, from frozen research to a local review pack."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import wave

from .contracts import ROOT, digest, instant, iso, load_json, utcnow
from .editorial import text, number
from .media import fingerprint, _load_stage, _save_stage, _srt_time, _scan, probe
from .local_lock import local_lock
from .research import verify

STAGES = ("research", "script", "storyboard", "voice", "render", "metadata")
VERSION = 2


def validate_script(story, research):
    if research["blockers"]:
        raise ValueError("Recherche bloquée : "+", ".join(research["blockers"]))
    for name in ("title", "angle", "audience", "sandbox_analysis"):
        text(story.get(name), name)
    claims = {c["claim_id"]: c for c in research["claims"]}
    beats = story.get("beats", [])
    if not isinstance(beats, list) or not beats:
        raise ValueError("Scénario vide.")
    if beats[0].get("role") != "hook" or beats[-1].get("role") != "conclusion":
        raise ValueError("Une accroche et une conclusion concrètes sont requises.")
    ids = set()
    for beat in beats:
        key = text(beat.get("beat_id"), "beat_id")
        if not re.fullmatch(r"[a-z0-9-]{1,60}", key) or key in ids:
            raise ValueError("Identifiant de scène invalide ou dupliqué.")
        ids.add(key)
        for name in ("narration", "heading", "role"):
            text(beat.get(name), name)
        if len(beat["heading"]) > 70:
            raise ValueError("Titre de scène trop long.")
        refs = beat.get("claim_ids", [])
        if not refs or set(refs)-claims.keys():
            raise ValueError("Chaque scène doit référencer les affirmations du dossier.")
        if beat.get("statement_kind") not in {"fact", "analysis", "hypothesis", "testimony"}:
            raise ValueError("Nature des propos de la scène requise.")
        if beat["statement_kind"] == "fact" and any(claims[k]["kind"] != "fact" or not claims[k]["verified"] for k in refs):
            raise ValueError("Une analyse ou un témoignage ne devient pas un fait confirmé.")
        visual = beat.get("visual", {})
        if visual.get("type") not in {"flow", "comparison", "timeline", "cards"}:
            raise ValueError("Composition flow, comparison, timeline ou cards requise.")
        labels = visual.get("labels", [])
        if not isinstance(labels, list) or not 2 <= len(labels) <= 4:
            raise ValueError("Deux à quatre éléments visuels requis.")
        for label in labels:
            if len(text(label, "label")) > 55:
                raise ValueError("Libellé visuel trop long.")
    metadata = story.get("metadata", {})
    titles = metadata.get("titles", [])
    if len(titles) != 3 or len(set(titles)) != 3 or any(not isinstance(t, str) or not 1 <= len(t) <= 100 for t in titles):
        raise ValueError("Trois titres distincts de moins de 101 caractères requis.")
    concepts = metadata.get("thumbnail_concepts", [])
    if len(concepts) < 3:
        raise ValueError("Trois concepts de miniature requis.")
    for concept in concepts:
        for name in ("hypothesis", "composition", "text", "evidence"):
            text(concept.get(name), name)
    if len({c["hypothesis"] for c in concepts}) != len(concepts):
        raise ValueError("Les concepts doivent tester des hypothèses distinctes.")
    text(metadata.get("description"), "description")
    return {"version": VERSION, "title": story["title"], "angle": story["angle"], "audience": story["audience"],
            "sandbox_analysis": story["sandbox_analysis"], "beats": beats, "metadata": metadata,
            "research_id": research["research_id"], "human_content_validation": "pending",
            "word_count": sum(len(b["narration"].split()) for b in beats)}


def storyboard(script, format_name):
    if format_name not in {"horizontal", "vertical"}:
        raise ValueError("Format horizontal ou vertical requis.")
    return {"version": VERSION, "format": format_name, "direction": "sandbox-diagrams-v1",
            "layout": "stacked" if format_name == "vertical" else "landscape",
            "scenes": [{**b, "transition": "slide_and_reveal", "caption_alignment": "sentence_audio",
                        "composition": "nodes_vertical" if format_name == "vertical" else "nodes_horizontal"} for b in script["beats"]]}


def spoken(text_value, pronunciations):
    result = text_value
    for term, alias in sorted(pronunciations.items(), key=lambda x: -len(x[0])):
        text(term, "pronunciation term")
        text(alias, "pronunciation alias")
        result = re.sub(r"(?<!\w)"+re.escape(term)+r"(?!\w)", lambda _: alias, result)
    return result


SAPI_SCRIPT = r'''param([string]$Request)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$requestData = Get-Content -LiteralPath $Request -Raw -Encoding UTF8 | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $synth.SelectVoice($requestData.voice)
  $synth.Rate = [int]$requestData.rate
  foreach ($item in $requestData.items) {
    $synth.SetOutputToWaveFile($item.path)
    $synth.Speak($item.text)
    $synth.SetOutputToNull()
  }
} finally { $synth.Dispose() }
'''


def audio_duration(path):
    with wave.open(str(path), "rb") as stream:
        return stream.getnframes() / stream.getframerate()


def join_waves(paths, output, *, pause=.18, pauses=None):
    """Concatenate takes; a silence follows each one (the same `pause`, or one value per take)."""
    gaps = list(pauses) if pauses is not None else [pause] * len(paths)
    if len(gaps) != len(paths):
        raise ValueError("Pauses et pistes de narration désalignées.")
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()
    with wave.open(str(output), "wb") as target:
        target.setparams(params)
        for path, gap in zip(paths, gaps):
            with wave.open(str(path), "rb") as source:
                if source.getparams()[:3] != params[:3]:
                    raise ValueError("Pistes de narration incompatibles.")
                target.writeframes(source.readframes(source.getnframes()))
            target.writeframes(b"\0" * round(params.framerate*gap)*params.nchannels*params.sampwidth)


def voice(board, options, directory, *, base):
    """Use a named stock system voice or explicitly licensed supplied recordings."""
    provider = options.get("provider", "system")
    if provider not in {"system", "recordings"}:
        raise ValueError("Fournisseur voix indisponible ; importer des WAV autorisés ou utiliser system.")
    if options.get("cloned") is not False:
        raise ValueError("Déclaration explicite cloned=false requise ; aucun clonage de voix.")
    text(options.get("authorization"), "voice authorization")
    rate = number(options.get("rate", 0), "voice rate", -5, 5)
    pronunciations = options.get("pronunciations", {})
    if not isinstance(pronunciations, dict):
        raise ValueError("Dictionnaire de prononciations requis.")
    items, scenes = [], []
    directory.mkdir(parents=True, exist_ok=True)
    for scene in board["scenes"]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", scene["narration"]) if s.strip()]
        rows = []
        for index, sentence in enumerate(sentences):
            path = directory / f"{scene['beat_id']}-{index}.wav"
            row = {"text": spoken(sentence, pronunciations), "caption": sentence, "path": str(path)}
            if provider == "recordings":
                recording = options.get("recordings", {}).get(scene["beat_id"], [])[index]
                source = (base / recording["path"]).resolve(strict=True)
                if fingerprint(source) != recording["sha256"]:
                    raise ValueError("Enregistrement voix modifié.")
                if source == path:
                    raise ValueError("La voix source doit rester hors des sorties.")
                shutil.copyfile(source, path)
            else:
                items.append(row)
            rows.append(row)
        scenes.append({"beat_id": scene["beat_id"], "sentences": rows})
    if provider == "system":
        if os.name != "nt" or not shutil.which("powershell.exe"):
            raise ValueError("system_voice_unavailable: Windows System.Speech requis ou recordings.")
        voice_name = text(options.get("name"), "system voice name")
        script_path = directory / "speak.ps1"
        script_path.write_text(SAPI_SCRIPT, encoding="utf-8-sig")
        request_path = directory / "speech-request.json"
        request_path.write_text(json.dumps({"voice": voice_name, "rate": rate, "items": items}, ensure_ascii=False), encoding="utf-8-sig")
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(script_path),
                                 "-Request", str(request_path)], capture_output=True, timeout=900)
        if result.returncode:
            raise ValueError("system_voice_unavailable: voix nommée non installée ou synthèse impossible.")
    cursor, artifacts = 0., []
    for scene in scenes:
        local = 0.
        scene["start_seconds"] = cursor
        for row in scene["sentences"]:
            duration = audio_duration(Path(row["path"]))
            if duration <= .05:
                raise ValueError("Piste vocale vide.")
            row.update(start_seconds=round(local, 4), end_seconds=round(local+duration, 4), sha256=fingerprint(Path(row["path"])))
            local += duration+.18
            artifacts.append({"path": row["path"], "sha256": row["sha256"]})
        target = directory / (scene["beat_id"]+".wav")
        join_waves([Path(s["path"]) for s in scene["sentences"]], target)
        duration = audio_duration(target)
        scene.update(path=str(target), sha256=fingerprint(target), duration_seconds=duration)
        artifacts.append({"path": str(target), "sha256": scene["sha256"]})
        cursor += duration
    if not 180 <= cursor <= 600:
        raise ValueError(f"Narration de {cursor:.1f}s hors de 180..600s ; réviser le scénario sans le remplir artificiellement.")
    return {"scenes": scenes, "duration_seconds": cursor, "provider": provider, "voice": options.get("name"),
            "cloned": False, "artifacts": artifacts, "alignment": "synthesized_sentence_boundaries",
            "review": "listening_and_pronunciation_pending"}


def metadata(script, research, audio):
    sources = "\n".join(s["title"]+" : "+s["url"] for s in research["sources"])
    starts = {s["beat_id"]: s["start_seconds"] for s in audio["scenes"]}
    chapters = [{"seconds": round(starts[b["beat_id"]], 2), "title": b["heading"]} for b in script["beats"]]
    return {**script["metadata"], "description": script["metadata"]["description"]+"\n\nSources\n"+sources,
            "chapters": chapters, "voice_disclosure": "Narration de synthèse avec une voix standard autorisée.",
            "native_experiment": "manual_studio_eligibility_check", "publication": "not_uploaded",
            "human_content_validation": "pending", "thumbnail_review": "pending"}


def _cached(path, identity):
    cached = _load_stage(path, identity)
    if cached:
        for artifact in cached.get("artifacts", []):
            if fingerprint(Path(artifact["path"])) != artifact["sha256"]:
                raise ValueError("Un artefact narratif terminé a été modifié ; aucun écrasement.")
    return cached


def run(store, config, story_path, *, stage="all", format_name="horizontal", draft=False, now=None):
    story_path = Path(story_path).resolve(strict=True)
    story = load_json(story_path)
    key = text(story.get("story_id"), "story_id")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", key):
        raise ValueError("story_id invalide.")
    if stage != "all" and stage not in STAGES:
        raise ValueError("Étape narrative inconnue.")
    base = story_path.parent
    research_path = (base / story["research"]).resolve(strict=True)
    dossier = load_json(research_path)
    research = verify(dossier, base=research_path.parent, now=now)
    # Snapshot hashes are verified before any cache lookup, even for metadata only.
    from .narrative_visuals import STYLE_VERSION, font_file
    logo_path = ROOT/"assets/brand/logo.png"
    try:
        font_hash = fingerprint(font_file())
    except ValueError:
        font_hash = None  # Research and scripting remain available without a render font.
    identity = {"version": VERSION, "renderer_version": STYLE_VERSION,
                "logo_sha256": fingerprint(logo_path) if logo_path.exists() else None, "font_sha256": font_hash,
                "story": story, "research": dossier,
                "direction": config.get("narrative", {}), "format": format_name, "draft": draft}
    revision = digest(identity)
    directory = store.directory / "narratives" / key / revision[:20]
    if story_path.is_relative_to(directory):
        raise ValueError("Le scénario source doit rester hors des sorties.")
    directory.mkdir(parents=True, exist_ok=True)
    # Preserve an executable source bundle whose references survive portable restore.
    frozen_dir = directory / "inputs"
    frozen_dir.mkdir(exist_ok=True)
    frozen_research = deepcopy(dossier)
    for source in frozen_research.get("sources", []):
        source["snapshot"] = str((research_path.parent / source["snapshot"]).resolve(strict=True))
    frozen_research_path = frozen_dir / "research.json"
    frozen_story = deepcopy(story)
    frozen_story["research"] = str(frozen_research_path)
    recording_inputs = []
    for recordings in frozen_story.get("voice", {}).get("recordings", {}).values():
        for recording in recordings:
            recording["path"] = str((base / recording["path"]).resolve(strict=True))
            if fingerprint(Path(recording["path"])) != recording["sha256"]:
                raise ValueError("Enregistrement voix modifié.")
            recording_inputs.append({"path": recording["path"], "sha256": recording["sha256"]})
    frozen_story_path = frozen_dir / "story.json"
    for path, content in ((frozen_research_path, frozen_research), (frozen_story_path, frozen_story)):
        encoded = json.dumps(content, ensure_ascii=False, indent=2)
        if path.exists():
            if path.read_text(encoding="utf-8") != encoded:
                raise ValueError("Entrée narrative archivée modifiée ; aucun écrasement.")
        else:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(encoded)
    result = {"story_id": key, "revision": revision, "format": format_name, "directory": str(directory),
              "episode_id": story.get("episode_id"), "opportunity_id": story.get("opportunity_id"),
              "synthetic": story.get("synthetic", False), "stages": {}, "publication": "not_uploaded",
              "inputs": [{"path": str(p), "sha256": fingerprint(p)} for p in (story_path, research_path, frozen_story_path, frozen_research_path)]+recording_inputs,
              "resume_story_path": str(frozen_story_path),
              "human_content_validation": "pending", "updated_at": iso(now or utcnow())}
    values = {}
    target = len(STAGES)-1 if stage == "all" else STAGES.index(stage)
    with local_lock(directory):
        for index, name in enumerate(STAGES[:target+1]):
            receipt = directory / (name+".json")
            stage_identity = {"revision": revision, "stage": name, "upstream": digest(values)}
            value = _cached(receipt, stage_identity)
            if name == "research" and value is not None and value.get("blockers") != research["blockers"]:
                value = None
            hit = value is not None
            if value is None:
                if name == "research":
                    value = research
                elif name == "script":
                    value = validate_script(story, values["research"])
                elif name == "storyboard":
                    value = storyboard(values["script"], format_name)
                elif name == "voice":
                    options = story.get("voice", {})
                    # Title, metadata and aspect ratio changes reuse the exact narration.
                    voice_identity = {"version": 1, "texts": [{"beat_id": b["beat_id"], "narration": b["narration"]} for b in story["beats"]],
                                      "options": options, "platform": os.name}
                    if options.get("provider") == "recordings":
                        for recordings in options.get("recordings", {}).values():
                            for recording in recordings:
                                if fingerprint((base / recording["path"]).resolve(strict=True)) != recording["sha256"]:
                                    raise ValueError("Enregistrement voix modifié.")
                        voice_identity["base"] = str(base)
                    voice_dir = store.directory / "narrative-cache" / "voice" / digest(voice_identity)[:20]
                    with local_lock(voice_dir):
                        shared_receipt = voice_dir / "voice.json"
                        value = _cached(shared_receipt, voice_identity)
                        if value is None:
                            value = voice(values["storyboard"], options, voice_dir, base=base)
                            _save_stage(shared_receipt, voice_identity, value)
                elif name == "render":
                    from .narrative_visuals import render
                    from .narrative_visuals import STYLE_VERSION, font_file
                    render_identity = {"version": STYLE_VERSION, "board": values["storyboard"], "audio": values["voice"], "draft": draft,
                                       "logo": fingerprint(ROOT/"assets/brand/logo.png"), "font": fingerprint(font_file())}
                    render_dir = store.directory / "narrative-cache" / "render" / digest(render_identity)[:20]
                    with local_lock(render_dir):
                        shared_receipt = render_dir / "render.json"
                        value = _cached(shared_receipt, render_identity)
                        if value is None:
                            value = render(values["storyboard"], values["voice"], render_dir, config, draft=draft)
                            _save_stage(shared_receipt, render_identity, value)
                else:
                    value = metadata(values["script"], values["research"], values["voice"])
                _save_stage(receipt, stage_identity, value)
            values[name] = value
            result["stages"][name] = {"receipt": str(receipt), "sha256": fingerprint(receipt), "cache": "hit" if hit else "miss", "status": value.get("status", "complete")}
            if name == "research" and value["blockers"]:
                result.update(status="blocked", blockers=value["blockers"])
                break
        else:
            result["status"] = "needs_review" if "render" in values else "prepared"
        result["asset"] = values.get("render")
        result["duration_seconds"] = values.get("voice", {}).get("duration_seconds")
        result["metadata"] = values.get("metadata")
        previous = store.get("narrative", key+":"+revision)
        if previous and result["status"] != "blocked":
            # A targeted rerun must not erase the later stages or their review.
            for name, saved in previous.get("stages", {}).items():
                if name not in result["stages"]:
                    if fingerprint(Path(saved["receipt"])) != saved["sha256"]:
                        raise ValueError("Étape narrative conservée modifiée.")
                    saved_receipt = load_json(Path(saved["receipt"]))
                    _cached(Path(saved["receipt"]), saved_receipt["identity"])
                    result["stages"][name] = saved
            for name in ("asset", "duration_seconds", "metadata"):
                if result.get(name) is None:
                    result[name] = previous.get(name)
            if result.get("asset"):
                result["status"] = "needs_review"
        result["review_revision"] = digest({"stages": {k: v["sha256"] for k,v in result["stages"].items()},
                                             "asset_sha256": (result["asset"] or {}).get("sha256")})
        if previous and previous.get("review", {}).get("revision") == result["review_revision"]:
            result.update(review=previous["review"], human_content_validation="approved")
        store.put("research", research["research_id"], research, episode_id=story.get("episode_id"), now=now)
        store.put("narrative", key+":"+revision, result, episode_id=story.get("episode_id"), now=now)
        store.event("narrative_stage_completed", key, {"revision": revision, "stage": stage, "status": result["status"]}, now=now)
    return result


def review(store, record_id, *, reviewer, evidence, checks, now=None):
    row = store.get("narrative", record_id)
    if not row or set(row["stages"]) != set(STAGES) or not row.get("asset"):
        raise ValueError("Production narrative complète requise avant validation.")
    text(reviewer, "reviewer")
    text(evidence, "review evidence")
    if set(checks) != {"facts", "editorial", "visual", "audio", "subtitles", "packaging"}:
        raise ValueError("Revue des faits, propos, images, son, sous-titres et packaging requise.")
    for stage in row["stages"].values():
        path = Path(stage["receipt"])
        if fingerprint(path) != stage["sha256"]:
            raise ValueError("Étape narrative modifiée depuis la production.")
        receipt = load_json(path)
        payload = _cached(path, receipt["identity"])
        if path.stem == "research":
            if payload.get("oral_verification_pending"):
                raise ValueError("Témoignage soutenu par transcription seulement ; confirmer l'écoute dans la recherche avant validation finale.")
            for source in payload["sources"]:
                if fingerprint(Path(source["snapshot"])) != source["sha256"]:
                    raise ValueError("Source documentaire modifiée depuis la production.")
    for artifact in row.get("inputs", []):
        if fingerprint(Path(artifact["path"])) != artifact["sha256"]:
            raise ValueError("Entrée narrative modifiée depuis la production.")
    frozen_story = load_json(Path(row["resume_story_path"]))
    dossier_path = Path(frozen_story["research"])
    current_research = verify(load_json(dossier_path), base=dossier_path.parent, now=now)
    if current_research["blockers"]:
        raise ValueError("Recherche bloquée avant validation : "+", ".join(current_research["blockers"]))
    row.update(human_content_validation="approved", review={"reviewer": reviewer, "evidence": evidence,
               "checks": sorted(set(checks)), "revision": row["review_revision"], "at": iso(now or utcnow())})
    store.put("narrative", record_id, row, episode_id=row.get("episode_id"), now=now)
    store.event("narrative_reviewed", record_id, row["review"], now=now)
    return row
