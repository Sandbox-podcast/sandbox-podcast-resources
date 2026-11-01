"""Validated editorial data; generated text never becomes a media command."""
from __future__ import annotations

import json
import math
import re

from .contracts import instant, utcnow

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
PLACEHOLDER = re.compile(r"\b(?:à développer|a developper|TODO|TBD|lorem ipsum)\b|\{\{", re.I)
MODES = {"documentary", "fiction", "mixed"}
STRUCTURES = {"human", "investigation", "idea"}
PROVIDERS = ("system", "voicestudio", "elevenlabs", "elevenlabs_browser", "recordings")
DEFAULT_SOUND_LEVEL_DB = {"music": -25., "effect": -15.}


def sound_level_db(cue, kind):
    """One rule for audio and render: documented level_db, legacy gain_db only if equal."""
    values = []
    for field in ("level_db", "gain_db"):
        if field in cue:
            value = cue[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not -60 <= value <= 0:
                raise ValueError("storytelling_sound_gain_invalid")
            values.append(float(value))
    if len(values) == 2 and abs(values[0] - values[1]) > 1e-9:
        raise ValueError("storytelling_sound_level_conflict")
    return values[0] if values else DEFAULT_SOUND_LEVEL_DB["music" if kind == "music" else "effect"]


def imported_sound_rights(source):
    """Rights declared at import authorize an imported sound; placeholders never do."""
    rights = (source or {}).get("rights")
    if (source or {}).get("media_type") != "audio" or not isinstance(rights, str) or not rights.strip() or rights.strip() == "usage_to_confirm":
        return None
    return rights.strip()


def required_text(value, field, *, maximum=20000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"Texte non vide requis : {field} (maximum {maximum} caractères).")
    if PLACEHOLDER.search(value):
        raise ValueError(f"Texte incomplet : {field}.")
    return value.strip()


def identity(value, field):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"Identifiant stable invalide : {field}.")
    return value


def _list(value, field):
    if not isinstance(value, list):
        raise ValueError(f"Liste requise : {field}.")
    return value


def _refs(value, known, field, *, required=False):
    refs = _list(value, field)
    if any(not isinstance(v, str) for v in refs) or len(set(refs)) != len(refs) or set(refs) - known:
        raise ValueError(f"Référence absente ou dupliquée : {field}.")
    if required and not refs:
        raise ValueError(f"Référence requise : {field}.")
    return refs


def _validate_script(script, sources):
    """Check structure and citations, without asserting factual or human review."""
    if not isinstance(script, dict) or script.get("version") != 1:
        raise ValueError("Scénario JSON version 1 requis.")
    # Reject non-JSON objects and non-finite numbers before any later cache key.
    try:
        result = json.loads(json.dumps(script, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError):
        raise ValueError("Le scénario contient une valeur JSON invalide.") from None
    identity(result.get("story_id"), "story_id")
    required_text(result.get("title"), "title", maximum=200)
    mode = result.get("mode")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError("Mode documentaire, fiction ou mixte requis.")
    budget = result.get("budget")
    if not isinstance(budget, dict) or type(budget.get("limit")) not in (int, float) or not math.isfinite(budget["limit"]) or budget["limit"] < 0:
        raise ValueError("Plafond de dépense explicite requis.")
    if not isinstance(budget.get("currency"), str) or not re.fullmatch(r"[A-Z]{3}", budget["currency"]):
        raise ValueError("Devise ISO explicite requise.")
    if "browser_credit_limit" in budget and (type(budget["browser_credit_limit"]) is not int or budget["browser_credit_limit"] < 0):
        raise ValueError("Plafond de crédits navigateur entier positif ou nul requis.")
    narrative = result.get("narrative", {})
    if not isinstance(narrative, dict) or not isinstance(narrative.get("structure"), str) or narrative["structure"] not in STRUCTURES:
        raise ValueError("Structure human, investigation ou idea requise.")
    for field in ("question", "interest", "vehicle", "initial", "answer"):
        required_text(narrative.get(field), "narrative." + field)
    continuity = result.get("continuity", {})
    if not isinstance(continuity, dict):
        raise ValueError("Fiche de continuité requise.")
    for field in ("characters", "locations", "chronology", "motifs"):
        _list(continuity.get(field), "continuity." + field)
    required_text(continuity.get("visual_style"), "continuity.visual_style")
    speakers = result.get("speakers")
    if not isinstance(speakers, dict) or not speakers:
        raise ValueError("Locuteurs et attribution des voix requis.")
    for key, speaker in speakers.items():
        identity(key, "speaker_id")
        if not isinstance(speaker, dict):
            raise ValueError("Locuteur invalide.")
        required_text(speaker.get("name"), "speaker.name", maximum=150)
        voice = speaker.get("voice", {})
        if not isinstance(voice, dict) or voice.get("provider") not in PROVIDERS:
            raise ValueError("Voix system, voicestudio, elevenlabs_browser, elevenlabs ou recordings requise.")
        required_text(voice.get("authorization"), "voice.authorization")
        if voice["provider"] == "system":
            required_text(voice.get("name"), "voice.name", maximum=200)
        elif voice["provider"] == "elevenlabs":
            required_text(voice.get("voice_id"), "voice.voice_id", maximum=200)
        elif voice["provider"] == "elevenlabs_browser":
            required_text(voice.get("name") or voice.get("voice_id"), "voice.browser_selection", maximum=200)
        elif voice["provider"] == "voicestudio":
            from .voicestudio import validate_voice
            validate_voice(voice)
    source_map = {}
    for source in _list(sources, "sources"):
        key = identity(source.get("source_id"), "source_id")
        if key in source_map:
            raise ValueError("Source dupliquée.")
        source_map[key] = source
    for speaker in speakers.values():
        voice = speaker["voice"]
        if any(key in voice for key in ("path", "command", "filter", "argv")):
            raise ValueError("Une voix ne peut contenir de commande ou chemin arbitraire.")
        if voice["provider"] == "recordings":
            recordings = voice.get("recordings")
            if not isinstance(recordings, dict) or not recordings:
                raise ValueError("Enregistrements par identifiant de réplique requis.")
            for uid, ref in recordings.items():
                identity(uid, "recording.utterance_id")
                if not isinstance(ref, dict) or set(ref) != {"source_id"}:
                    raise ValueError("Un enregistrement référence seulement un source_id importé.")
                source = source_map.get(ref["source_id"])
                if not source or source.get("media_type") != "audio" or source.get("rights") in (None, "", "usage_to_confirm"):
                    raise ValueError("Enregistrement audio autorisé absent des sources.")
    facts = {}
    for fact in _list(result.get("facts"), "facts"):
        if not isinstance(fact, dict):
            raise ValueError("Fiche de fait invalide.")
        key = identity(fact.get("fact_id"), "fact_id")
        if key in facts:
            raise ValueError("Fait dupliqué.")
        required_text(fact.get("text"), "fact.text")
        status = fact.get("status")
        if status not in ("source_supported", "confirmed", "uncertain", "disputed", "fiction"):
            raise ValueError("Statut documentaire du fait requis.")
        refs = _refs(fact.get("source_ids", []), source_map.keys(), "fact.source_ids", required=status != "fiction")
        quotes = _list(fact.get("quotes", []), "fact.quotes")
        quoted = set()
        for ref in quotes:
            if not isinstance(ref, dict) or ref.get("source_id") not in refs:
                raise ValueError("Citation reliée à une source du fait requise.")
            quote = required_text(ref.get("quote"), "fact.quote")
            source = source_map[ref["source_id"]]
            if quote not in source.get("text", ""):
                raise ValueError("Citation absente du document importé.")
            quoted.add(ref["source_id"])
        if status != "fiction" and set(refs) - quoted:
            raise ValueError("Chaque source du fait doit avoir une citation exacte.")
        if mode == "documentary" and status == "fiction":
            raise ValueError("Un fait fictif est interdit dans un documentaire.")
        if status == "confirmed":
            verification = fact.get("verification", {})
            if not isinstance(verification, dict):
                raise ValueError("Preuve de vérification requise.")
            for field in ("reviewer", "reason", "evidence"):
                required_text(verification.get(field), "verification." + field)
            try:
                checked = instant(verification.get("checked_at", ""))
            except (ValueError, TypeError):
                raise ValueError("Date de vérification avec fuseau requise.") from None
            if checked > utcnow():
                raise ValueError("Vérification future interdite.")
            if not any(source_map[s].get("kind") == "primary" for s in refs):
                raise ValueError("Un fait confirmé demande une source primaire.")
            if not any(source_map[s].get("verification") == verification for s in refs):
                raise ValueError("Une vérification confirmée doit être fournie dans les métadonnées importées, pas inventée par le scénario.")
        facts[key] = fact
    scenes = _list(result.get("scenes"), "scenes")
    if not scenes or len(scenes) > 500:
        raise ValueError("Une à cinq cents scènes requises.")
    scene_ids, utterance_ids, shot_ids = set(), set(), set()
    words = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Scène invalide.")
        sid = identity(scene.get("scene_id"), "scene_id")
        if sid in scene_ids:
            raise ValueError("Scène dupliquée.")
        scene_ids.add(sid)
        if type(scene.get("version")) is not int or scene["version"] < 1:
            raise ValueError("Version de scène positive requise.")
        for field in ("function", "knowledge_before", "knowledge_after"):
            required_text(scene.get(field), "scene." + field)
        if scene["knowledge_before"].strip().casefold() == scene["knowledge_after"].strip().casefold():
            raise ValueError("La scène doit faire évoluer la compréhension ou l'attente.")
        factual = scene.get("factual_status")
        if factual not in ("fact", "fiction", "reconstruction") or mode == "documentary" and factual != "fact":
            raise ValueError("Statut factuel de scène incompatible avec le mode.")
        if factual == "reconstruction":
            required_text(scene.get("reconstruction_notice"), "reconstruction_notice")
        fact_refs = _refs(scene.get("fact_ids", []), facts.keys(), "scene.fact_ids", required=factual == "fact")
        if factual == "fact" and any(facts[f]["status"] == "fiction" for f in fact_refs):
            raise ValueError("Un passage factuel ne peut citer un fait fictif.")
        utterances = _list(scene.get("utterances"), "scene.utterances")
        if not utterances:
            raise ValueError("Texte oral intégral requis pour chaque scène.")
        local_ids = set()
        for utterance in utterances:
            if not isinstance(utterance, dict):
                raise ValueError("Réplique invalide.")
            uid = identity(utterance.get("utterance_id"), "utterance_id")
            if uid in utterance_ids:
                raise ValueError("Réplique dupliquée.")
            utterance_ids.add(uid)
            local_ids.add(uid)
            speaker = utterance.get("speaker_id")
            if not isinstance(speaker, str) or speaker not in speakers:
                raise ValueError("Locuteur de réplique inconnu.")
            if speakers[speaker]["voice"]["provider"] == "recordings" and uid not in speakers[speaker]["voice"]["recordings"]:
                raise ValueError("Enregistrement manquant pour la réplique.")
            spoken = required_text(utterance.get("text"), "utterance.text", maximum=20000)
            if re.search(r"https?://|\[(?:pause|music|musique|montage|whisper|laugh|sigh|bruitage)[^\]]*\]", spoken, re.I):
                raise ValueError("URL et consignes techniques interdites dans le texte prononcé.")
            if spoken.casefold().startswith(speakers[speaker]["name"].casefold() + ":"):
                raise ValueError("Le nom du locuteur doit rester séparé du texte prononcé.")
            if not isinstance(utterance.get("delivery", {}), dict):
                raise ValueError("Intentions de jeu structurées requises.")
            if speakers[speaker].get("real_person"):
                source = source_map.get(utterance.get("verbatim_source_id"))
                if not source or spoken not in source.get("text", ""):
                    raise ValueError("Paroles d'une personne réelle : citation exacte et source requises.")
            words += len(spoken.split())
        shots = _list(scene.get("shots"), "scene.shots")
        covered = set()
        if not shots:
            raise ValueError("Découpage visuel requis.")
        for shot in shots:
            if not isinstance(shot, dict):
                raise ValueError("Plan invalide.")
            key = identity(shot.get("shot_id"), "shot_id")
            if key in shot_ids:
                raise ValueError("Plan dupliqué.")
            shot_ids.add(key)
            covered.update(_refs(shot.get("utterance_ids"), local_ids, "shot.utterance_ids", required=True))
            required_text(shot.get("description"), "shot.description")
            if shot.get("purpose") not in ("proof", "explanation", "situation", "emotion", "transition"):
                raise ValueError("Fonction visuelle explicite requise.")
            if shot.get("type") not in ("diagram", "image", "video"):
                raise ValueError("Type de plan diagram, image ou video requis.")
            if shot["type"] == "diagram":
                labels = _list(shot.get("labels"), "shot.labels")
                if not 1 <= len(labels) <= 6:
                    raise ValueError("Un à six libellés de schéma requis.")
                for label in labels:
                    required_text(label, "shot.label", maximum=150)
                if shot["purpose"] == "proof":
                    raise ValueError("Un schéma explicatif ne constitue pas une preuve.")
            else:
                source = source_map.get(shot.get("source_id"))
                if not source or source.get("media_type") != shot["type"]:
                    raise ValueError("Média du plan absent ou incompatible.")
                if source.get("rights") in (None, "", "usage_to_confirm"):
                    raise ValueError("Droits d'usage du média à renseigner.")
                if shot["purpose"] == "proof" and source.get("generated"):
                    raise ValueError("Une illustration générée ne constitue pas une preuve.")
            if "path" in shot or "command" in shot or "filter" in shot:
                raise ValueError("Un plan référence une ressource importée, jamais une commande ou un chemin arbitraire.")
        if local_ids - covered:
            raise ValueError("Chaque passage oral doit être couvert par un plan.")
        sound = scene.get("sound", {})
        if not isinstance(sound, dict):
            raise ValueError("Direction sonore structurée requise.")
        cues = []
        if sound.get("music"):
            cues.append(sound["music"])
        cues.extend(_list(sound.get("effects", []), "sound.effects"))
        for cue in cues:
            if not isinstance(cue, dict):
                raise ValueError("Indication sonore structurée requise.")
            if any(key in cue for key in ("path", "command", "filter", "argv")):
                raise ValueError("Un son référence une source importée ou une intention, jamais une commande.")
            required_text(cue.get("purpose"), "sound.purpose")
            try:
                sound_level_db(cue, "music" if sound.get("music") is cue else "effect")
            except ValueError:
                raise ValueError("Niveau sonore invalide : level_db entre -60 et 0 dB ; un ancien gain_db doit lui être identique.") from None
            if cue.get("provider") == "recordings":
                if not imported_sound_rights(source_map.get(cue.get("source_id"))):
                    raise ValueError("Source sonore autorisée absente.")
            else:
                required_text(cue.get("prompt"), "sound.prompt")
    result["editorial_metrics"] = {"spoken_words": words, "estimated_speech_seconds": round(words / 155 * 60, 3),
                                    "timing_status": "estimated_until_audio_measured"}
    result["content_review"] = {"status": "pending", "validation": "structure_and_citations_only"}
    return result


def validate_script(script, sources):
    """Expose malformed structured input as a business error, never a traceback."""
    try:
        return _validate_script(script, sources)
    except (KeyError, TypeError, AttributeError):
        raise ValueError("Structure du scénario ou des références invalide.") from None


SCRIPT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
    "required": ["version", "story_id", "title", "mode", "budget", "narrative", "speakers", "continuity", "facts", "scenes"],
    "properties": {"version": {"const": 1}, "story_id": {"$ref": "#/$defs/id"},
                   "title": {"type": "string", "minLength": 1}, "mode": {"enum": sorted(MODES)},
                   "budget": {"type": "object", "required": ["limit", "currency"], "properties": {
                       "limit": {"type": "number", "minimum": 0}, "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
                       "browser_credit_limit": {"type": "integer", "minimum": 0}}},
                   "narrative": {"type": "object", "required": ["question", "interest", "vehicle", "initial", "answer", "structure"],
                       "properties": {**{f: {"$ref": "#/$defs/text"} for f in ("question", "interest", "vehicle", "initial", "answer")},
                                      "structure": {"enum": sorted(STRUCTURES)}}},
                   "speakers": {"type": "object", "minProperties": 1, "additionalProperties": {"$ref": "#/$defs/speaker"}},
                   "continuity": {"type": "object", "required": ["characters", "locations", "chronology", "visual_style", "motifs"],
                       "properties": {**{f: {"type": "array", "items": {"type": "string"}} for f in ("characters", "locations", "chronology", "motifs")},
                                      "visual_style": {"$ref": "#/$defs/text"}}},
                   "facts": {"type": "array", "items": {"$ref": "#/$defs/fact"}},
                   "scenes": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/scene"}}},
    "$defs": {
        "id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$"},
        "text": {"type": "string", "minLength": 1, "maxLength": 20000},
        "ids": {"type": "array", "uniqueItems": True, "items": {"$ref": "#/$defs/id"}},
        "speaker": {"type": "object", "required": ["name", "voice"], "properties": {
            "name": {"$ref": "#/$defs/text"}, "real_person": {"type": "boolean"},
            "voice": {"type": "object", "required": ["provider", "authorization"], "properties": {
                "provider": {"enum": list(PROVIDERS)}, "authorization": {"$ref": "#/$defs/text"},
                "name": {"type": "string"}, "voice_id": {"type": "string"}, "model_id": {"type": "string"},
                **{f: {"type": "string"} for f in ("profile_id", "engine", "language", "profile_revision", "voicestudio_version")},
                "settings": {"type": "object"},
                "pronunciations": {"type": "object", "additionalProperties": {"type": "string"}},
                "recordings": {"type": "object", "additionalProperties": {"type": "object", "required": ["source_id"],
                    "additionalProperties": False, "properties": {"source_id": {"$ref": "#/$defs/id"}}}}}}}},
        "fact": {"type": "object", "required": ["fact_id", "text", "source_ids", "status"], "properties": {
            "fact_id": {"$ref": "#/$defs/id"}, "text": {"$ref": "#/$defs/text"}, "source_ids": {"$ref": "#/$defs/ids"},
            "status": {"enum": ["source_supported", "confirmed", "uncertain", "disputed", "fiction"]},
            "quotes": {"type": "array", "items": {"type": "object", "required": ["source_id", "quote"],
                "properties": {"source_id": {"$ref": "#/$defs/id"}, "quote": {"$ref": "#/$defs/text"}}}},
            "verification": {"type": "object", "required": ["reviewer", "reason", "evidence", "checked_at"],
                "properties": {f: {"type": "string"} for f in ("reviewer", "reason", "evidence", "checked_at")}}}},
        "utterance": {"type": "object", "required": ["utterance_id", "speaker_id", "text", "delivery"], "properties": {
            "utterance_id": {"$ref": "#/$defs/id"}, "speaker_id": {"$ref": "#/$defs/id"}, "text": {"$ref": "#/$defs/text"},
            "verbatim_source_id": {"$ref": "#/$defs/id"}, "delivery": {"type": "object", "properties": {
                "emotion": {"type": "string"}, "pace": {"type": "string"}, "intensity": {"type": "string"},
                "pause_after_seconds": {"type": "number", "minimum": 0, "maximum": 10}}}}},
        "shot": {"type": "object", "required": ["shot_id", "utterance_ids", "description", "purpose", "type"], "properties": {
            "shot_id": {"$ref": "#/$defs/id"}, "utterance_ids": {"$ref": "#/$defs/ids"}, "description": {"$ref": "#/$defs/text"},
            "purpose": {"enum": ["proof", "explanation", "situation", "emotion", "transition"]},
            "type": {"enum": ["diagram", "image", "video"]}, "labels": {"type": "array", "minItems": 1, "maxItems": 6, "items": {"type": "string"}},
            "source_id": {"$ref": "#/$defs/id"}, "composition": {"type": "string"}, "movement": {"type": "string"},
            "transition": {"type": "string"}, "on_screen_text": {"type": "string"}}},
        "cue": {"type": "object", "required": ["purpose"], "properties": {
            "purpose": {"$ref": "#/$defs/text"}, "provider": {"enum": ["elevenlabs", "elevenlabs_browser", "recordings"]},
            "prompt": {"$ref": "#/$defs/text"}, "source_id": {"$ref": "#/$defs/id"},
            "duration_seconds": {"type": "number", "exclusiveMinimum": 0}, "offset_seconds": {"type": "number", "minimum": 0},
            "level_db": {"type": "number", "minimum": -60, "maximum": 0}, "loop": {"type": "boolean"}}},
        "scene": {"type": "object", "required": ["scene_id", "version", "function", "knowledge_before", "knowledge_after", "factual_status", "fact_ids", "utterances", "shots", "sound"],
            "properties": {"scene_id": {"$ref": "#/$defs/id"}, "version": {"type": "integer", "minimum": 1},
                **{f: {"$ref": "#/$defs/text"} for f in ("function", "knowledge_before", "knowledge_after")},
                "factual_status": {"enum": ["fact", "fiction", "reconstruction"]}, "fact_ids": {"$ref": "#/$defs/ids"},
                "reconstruction_notice": {"$ref": "#/$defs/text"}, "utterances": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/utterance"}},
                "shots": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/shot"}},
                "sound": {"type": "object", "properties": {"music": {"$ref": "#/$defs/cue"}, "effects": {"type": "array", "items": {"$ref": "#/$defs/cue"}}}}}},
    },
}
