"""Local Voice Studio API: profile discovery, verified controls and speech takes."""
from __future__ import annotations

from http.client import HTTPException
import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from .contracts import digest

DEFAULT_URL = "http://127.0.0.1:3900"

# The API lists engines and their declared capabilities, not which /generate
# fields each adapter applies. These rows come from reading the 0.5.7 backend:
# api/routers/generation.py, services/tts_backend.py, engines/voxcpm2_subprocess
# and engines/omnivoice_subprocess. Any other version keeps those controls unverified.
VERIFIED_CONTROLS = {
    "0.5.7": {
        "voxcpm2": {"speed": False, "duration": False, "seed": True, "num_step": True, "guidance_scale": True,
                    "instruct": "freeform_changes_clone_mode"},
        "omnivoice": {"speed": True, "duration": True, "seed": True, "num_step": True, "guidance_scale": True,
                      "instruct": "voice_design_tags"},
        "omnivoice-subprocess": {"speed": True, "duration": True, "seed": True, "num_step": True, "guidance_scale": True,
                                 "instruct": "voice_design_tags"},
        "kittentts": {"speed": True, "duration": False, "seed": None, "num_step": False, "guidance_scale": False,
                      "instruct": "ignored"},
    },
}
# Which engine flag a profile kind needs: a clone needs a reference-audio engine, a design a describable one.
PROFILE_ENGINE_FLAG = {"clone": "supports_cloning", "design": "supports_voice_design"}
CONTROL_NOTES = {
    "speed_false": "Le moteur reçoit le champ speed mais ne l'applique pas : adapter le débit par le texte (phrases, ponctuation, pauses).",
    "speed_none": "Application de speed non vérifiée pour ce moteur ou cette version : ne pas l'utiliser.",
    "ignored": "Le moteur reçoit la consigne mais l'ignore : voix préréglées, sans direction.",
    "freeform_changes_clone_mode": "Une consigne libre précède le texte ; avec un profil cloné, elle remplace la continuation sur l'enregistrement de référence par un clonage contrôlé. Comparer la ressemblance sur un court passage avant de l'adopter.",
    "voice_design_tags": "La consigne accepte seulement le vocabulaire fermé de conception de voix (genre, âge, hauteur, accent). Elle décrit le timbre, pas l'interprétation ; ne pas l'utiliser avec une voix clonée.",
    "instruct_none": "Effet de la consigne non vérifié pour ce moteur ou cette version.",
    "effect_preset": "Traitement audio appliqué après la synthèse (égalisation, compression, réverbération) : il ne change ni la prosodie ni l'intention.",
}
INTERPRETATION = {
    "documentary": {"intent": "Narration documentaire posée : débit mesuré, sérieux sans gravité forcée, transitions audibles.",
                    "text": ["Phrases de longueur moyenne, une information principale par phrase.",
                             "Ponctuation qui place les respirations ; pause marquée aux changements de scène.",
                             "Chiffres, sigles et noms propres écrits comme ils doivent être prononcés."],
                    "effect_preset": "broadcast", "speed": None, "instruct": "calm, measured documentary narration"},
    "explainer": {"intent": "Explication claire et vivante, ton de conversation, chaque étape bien détachée.",
                  "text": ["Phrases courtes, une idée par phrase, définitions au moment utile.",
                           "Questions rhétoriques rares, chacune suivie de sa réponse.",
                           "Mots de liaison explicites entre les étapes."],
                  "effect_preset": "broadcast", "speed": None, "instruct": "clear, friendly explanatory tone"},
    "commentary": {"intent": "Chronique argumentée : ton direct, opinions annoncées comme telles, nuances audibles.",
                   "text": ["Phrases affirmatives courtes, opinions signalées par leur auteur.",
                            "Relances et contrastes portés par la syntaxe plutôt que par des adverbes.",
                            "Conclusion de chaque argument avant le suivant."],
                   "effect_preset": "podcast", "speed": None, "instruct": "direct, engaged commentary"},
    "commentary_dynamic": {"intent": "Commentaire dynamique, de type sportif : énergie élevée, relances rapides, montées de tension.",
                           "text": ["Phrases très courtes au présent, verbes d'action, sujets explicites.",
                                    "Exclamations mesurées, réservées aux moments forts.",
                                    "Énumérations rythmées ; une respiration courte entre les relances."],
                           "effect_preset": "bright", "speed": 1.08, "instruct": "energetic, fast-paced live sports commentary"},
    "fiction": {"intent": "Récit incarné : variations d'intensité selon les scènes, dialogues distincts du narrateur.",
                "text": ["Répliques séparées par personnage, chacune avec son intention dans delivery.",
                         "Rythme varié : phrases brèves dans l'action, plus longues dans la description.",
                         "Aucune didascalie ni nom de personnage dans le texte prononcé."],
                "effect_preset": "cinematic", "speed": None, "instruct": "immersive storytelling narration"},
}
INTERPRETATION["docufiction"] = {**INTERPRETATION["documentary"],
    "intent": "Narration documentaire posée, avec des reconstitutions annoncées et jouées plus près des personnages."}
SETTING_LIMITS = {"seed": (0, 2**31-1), "num_step": (1, 64), "guidance_scale": (.1, 20.), "speed": (.7, 1.3),
                  "pause_between_sentences_seconds": (0., 1.5)}
PROFILE_FIELDS = ("id", "name", "kind", "language", "ref_audio_path", "audio_url", "ref_text", "is_locked",
                  "locked_audio_path", "seed", "instruct")


class VoiceStudioError(ValueError):
    """Stable error code in str(); provider detail kept apart for the operator."""
    def __init__(self, code, detail=None):
        super().__init__(code)
        self.detail = detail


class VoiceStudio:
    def __init__(self, base_url=DEFAULT_URL, *, timeout=1800):
        parts = urlsplit(base_url)
        if parts.scheme != "http" or parts.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise VoiceStudioError("voicestudio_loopback_url_required", base_url)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _call(self, path, *, form=None, timeout=None):
        data = urlencode(form).encode("utf-8") if form is not None else None
        request = Request(self.base_url + path, data=data, method="POST" if form is not None else "GET",
                          headers={"Content-Type": "application/x-www-form-urlencoded"} if form is not None else {})
        try:
            with urlopen(request, timeout=timeout or self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except HTTPError as error:
            body = error.read()[:2000].decode("utf-8", "replace")
            try:
                detail = json.loads(body).get("detail", body)
            except (ValueError, AttributeError):
                detail = body
            code = {403: "voicestudio_engine_license_required", 422: "voicestudio_request_rejected",
                    503: "voicestudio_engine_not_ready_retry"}.get(error.code, "voicestudio_http_error")
            raise VoiceStudioError(code, str(detail)[:500]) from None
        except (URLError, OSError, HTTPException) as error:
            raise VoiceStudioError("voicestudio_unavailable", str(getattr(error, "reason", error))[:300]) from None

    def json(self, path, *, timeout=15):
        body, _ = self._call(path, timeout=timeout)
        try:
            return json.loads(body)
        except ValueError:
            raise VoiceStudioError("voicestudio_unexpected_response", path) from None

    def generate(self, fields):
        body, content_type = self._call("/generate", form=fields)
        if body[:4] != b"RIFF" or body[8:12] != b"WAVE":
            raise VoiceStudioError("voicestudio_unexpected_response", content_type)
        return body


def profile_revision(profile):
    return digest({key: profile.get(key) for key in PROFILE_FIELDS})


def consent(profile):
    if profile.get("is_demo"):
        return "demo_voice"
    if profile.get("consent_basis") == "own_voice" and profile.get("consent_attested_at"):
        return "own_voice_attested"
    if profile.get("consent_basis") or profile.get("verified_own_voice"):
        return "declared_" + str(profile.get("consent_basis") or "own_voice")
    return "not_recorded"


def controls(version, engine):
    """Controls verified for this exact version and engine; unknown ones stay None."""
    row = VERIFIED_CONTROLS.get(version, {}).get(engine, {})
    return {key: row.get(key) for key in ("speed", "duration", "seed", "num_step", "guidance_scale", "instruct")}


def _usable(engine, kind):
    flag = PROFILE_ENGINE_FLAG.get(kind)
    return not flag or bool(engine.get(flag))


def discover(client):
    """Read-only inventory. Personal reference text and file paths never leave Voice Studio."""
    try:
        health = client.json("/health")
        profiles = client.json("/profiles")
        engines = client.json("/engines/tts")
        presets = client.json("/engines/effects/presets").get("presets", [])
    except VoiceStudioError as error:
        return {"status": "unavailable", "error": str(error), "detail": error.detail, "base_url": client.base_url}
    if health.get("status") != "ok" or not isinstance(profiles, list) or not isinstance(engines.get("backends"), list):
        return {"status": "unavailable", "error": "voicestudio_unexpected_response", "base_url": client.base_url}
    version = str(health.get("version"))
    available = [e for e in engines["backends"] if e.get("available")]
    engine_rows = [{"id": e["id"], "name": e.get("display_name"), "cloning": e.get("supports_cloning"),
                    "voice_design": e.get("supports_voice_design"), "emotion": e.get("supports_emotion"),
                    "instruct_vocabulary": e.get("instruct_vocabulary"), "device": e.get("effective_device"),
                    "preset_voices": e.get("preset_voices") or [], "verified_controls": controls(version, e["id"])}
                   for e in available]
    rows = []
    for profile in profiles:
        kind = profile.get("kind") or "clone"
        usable = [e["id"] for e in available if _usable(e, kind)]
        rows.append({"profile_id": profile["id"], "name": profile.get("name"), "kind": kind,
                     "language": profile.get("language"), "consent": consent(profile),
                     "locked": bool(profile.get("is_locked")), "revision": profile_revision(profile),
                     "usable_engines": usable})
    return {"status": "available", "base_url": client.base_url, "version": version, "device": health.get("device"),
            "active_engine": engines.get("active"), "profiles": rows, "engines": engine_rows,
            "effect_presets": [{"id": p["id"], "label": p.get("label"), "description": p.get("description")} for p in presets],
            "verification": "verified_controls" if version in VERIFIED_CONTROLS else "controls_unverified_for_this_version"}


def interpretation_plan(video_type, engine, version, *, register=None, presets=None):
    """Separate identity, direction and processing; only verified engine controls are applied."""
    key = "commentary_dynamic" if video_type == "commentary" and register == "dynamic" else video_type
    base = INTERPRETATION.get(key, INTERPRETATION["documentary"])
    verified = controls(version, engine)
    applied, unsupported, trials = {}, [], []
    if base["speed"] is not None:
        if verified["speed"] is True:
            applied["speed"] = base["speed"]
        else:
            unsupported.append({"control": "speed", "wanted": base["speed"],
                                "reason": CONTROL_NOTES["speed_false" if verified["speed"] is False else "speed_none"]})
    mode = verified["instruct"]
    if mode == "freeform_changes_clone_mode":
        trials.append({"control": "instruct", "value": base["instruct"], "reason": CONTROL_NOTES[mode]})
    else:
        unsupported.append({"control": "instruct", "wanted": base["instruct"],
                            "reason": CONTROL_NOTES.get(mode, CONTROL_NOTES["instruct_none"])})
    names = {p["id"] for p in presets or []}
    preset = base["effect_preset"] if not names or base["effect_preset"] in names else "broadcast"
    # A fixed seed keeps a regenerated take comparable; only sent where it is applied.
    sampling = {key: value for key, value in (("seed", 42), ("num_step", 16)) if verified[key] is True}
    return {"video_type": video_type, "register": register, "engine": engine, "voicestudio_version": version,
            "direction": {"intent": base["intent"], "text_adaptations": base["text"]},
            "engine_controls": {"verified": verified, "applied": applied, "not_applied": unsupported, "optional_trials": trials},
            "processing": {"effect_preset": preset, "note": CONTROL_NOTES["effect_preset"]},
            "settings": {**sampling, "effect_preset": preset, "pause_between_sentences_seconds": .3, **applied}}


def _number(value, key):
    low, high = SETTING_LIMITS[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise VoiceStudioError("voicestudio_setting_invalid", key)
    if key in {"seed", "num_step"} and type(value) is not int:
        raise VoiceStudioError("voicestudio_setting_invalid", key)
    return value


def validate_voice(voice):
    """Structure only; live compatibility is checked against the running API before synthesis."""
    for key in ("profile_id", "engine", "language", "profile_revision", "voicestudio_version"):
        if not isinstance(voice.get(key), str) or not voice[key].strip() or len(voice[key]) > 200:
            raise VoiceStudioError("voicestudio_voice_incomplete", key)
    settings = voice.get("settings", {})
    if not isinstance(settings, dict):
        raise VoiceStudioError("voicestudio_setting_invalid", "settings")
    unknown = set(settings) - {"seed", "num_step", "guidance_scale", "speed", "instruct", "effect_preset", "pause_between_sentences_seconds"}
    if unknown:
        raise VoiceStudioError("voicestudio_setting_unknown", ", ".join(sorted(unknown)))
    for key in SETTING_LIMITS:
        if key in settings:
            _number(settings[key], key)
    for key in ("instruct", "effect_preset"):
        if key in settings and (not isinstance(settings[key], str) or not settings[key].strip() or len(settings[key]) > 300 or "\n" in settings[key]):
            raise VoiceStudioError("voicestudio_setting_invalid", key)
    return voice


def check_compatibility(voice, version):
    """Refuse a control that the selected engine does not apply in this Voice Studio version."""
    verified = controls(version, voice["engine"])
    settings = voice.get("settings", {})
    if settings.get("speed") is not None and verified["speed"] is not True:
        raise VoiceStudioError("voicestudio_speed_not_applied_by_engine", voice["engine"])
    if settings.get("instruct") and verified["instruct"] != "freeform_changes_clone_mode":
        raise VoiceStudioError("voicestudio_instruct_not_supported_by_engine", voice["engine"])
    for key in ("seed", "num_step", "guidance_scale"):
        if key in settings and verified[key] is not True:
            raise VoiceStudioError("voicestudio_control_unverified", key)


def live_voice(client, voice):
    """Check the pinned profile and engine against the running service before a new take."""
    validate_voice(voice)
    health = client.json("/health")
    if health.get("status") != "ok":
        raise VoiceStudioError("voicestudio_unavailable", "health")
    version = str(health.get("version"))
    # The pinned settings were planned for one version; a newer service is re-read before any take.
    if version != voice["voicestudio_version"]:
        raise VoiceStudioError("voicestudio_version_changed_select_again", version)
    profile = next((p for p in client.json("/profiles") if p.get("id") == voice["profile_id"]), None)
    if profile is None:
        raise VoiceStudioError("voicestudio_profile_missing", voice["profile_id"])
    if profile_revision(profile) != voice["profile_revision"]:
        raise VoiceStudioError("voicestudio_profile_changed_select_again", voice["profile_id"])
    engine = next((e for e in client.json("/engines/tts").get("backends", []) if e.get("id") == voice["engine"]), None)
    if not engine or not engine.get("available"):
        raise VoiceStudioError("voicestudio_engine_unavailable", voice["engine"])
    kind = profile.get("kind") or "clone"
    if not _usable(engine, kind):
        raise VoiceStudioError("voicestudio_engine_cannot_clone" if kind == "clone" else "voicestudio_engine_not_usable_for_profile", voice["engine"])
    presets = {p["id"] for p in client.json("/engines/effects/presets").get("presets", [])}
    settings = voice.get("settings", {})
    if settings.get("effect_preset", "broadcast") not in presets:
        raise VoiceStudioError("voicestudio_effect_preset_unknown", settings.get("effect_preset"))
    check_compatibility(voice, version)
    return {"version": version, "profile_name": profile.get("name"), "consent": consent(profile)}


def request_fields(voice, text):
    settings = voice.get("settings", {})
    fields = {"text": text, "profile_id": voice["profile_id"], "engine": voice["engine"], "language": voice["language"],
              "effect_preset": settings.get("effect_preset", "broadcast"), "wav_bits": "16",
              "max_chunk_chars": "400", "pronounce": "true"}
    for key in ("seed", "num_step", "guidance_scale", "instruct", "speed"):
        if key in settings:
            fields[key] = str(settings[key])
    return fields


def selection(discovery, profile_id, *, engine=None, video_type="documentary", register=None, authorization=None,
              settings=None, pronunciations=None):
    """Turn an explicit user choice into the pinned speaker voice of a story."""
    if discovery.get("status") != "available":
        raise VoiceStudioError("voicestudio_unavailable", discovery.get("detail"))
    profile = next((p for p in discovery["profiles"] if p["profile_id"] == profile_id), None)
    if profile is None:
        raise VoiceStudioError("voicestudio_profile_missing", profile_id)
    engine = engine or (discovery["active_engine"] if discovery["active_engine"] in profile["usable_engines"] else None)
    if engine not in profile["usable_engines"]:
        raise VoiceStudioError("voicestudio_engine_not_usable_for_profile", str(engine))
    if profile["consent"] == "not_recorded" and not (isinstance(authorization, str) and authorization.strip()):
        raise VoiceStudioError("voicestudio_authorization_required", profile_id)
    plan = interpretation_plan(video_type, engine, discovery["version"], register=register, presets=discovery["effect_presets"])
    basis = {"own_voice_attested": "consentement « voix personnelle » attesté dans Voice Studio",
             "demo_voice": "voix de démonstration fournie avec Voice Studio"}.get(profile["consent"], profile["consent"])
    chosen = {**plan["settings"], **{k: v for k, v in (settings or {}).items() if v is not None}}
    if chosen["effect_preset"] not in {p["id"] for p in discovery["effect_presets"]}:
        raise VoiceStudioError("voicestudio_effect_preset_unknown", chosen["effect_preset"])
    words = pronunciations or {}
    if not isinstance(words, dict) or any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip() for k, v in words.items()):
        raise VoiceStudioError("voicestudio_pronunciations_invalid")
    voice = {"provider": "voicestudio", "profile_id": profile_id, "name": profile["name"], "engine": engine,
             "language": profile["language"] or "French", "profile_revision": profile["revision"],
             "voicestudio_version": discovery["version"], "settings": chosen, "pronunciations": dict(words),
             "authorization": (authorization or "").strip() or f"Profil Voice Studio « {profile['name']} » ({profile_id}) : {basis}."}
    validate_voice(voice)
    check_compatibility(voice, discovery["version"])
    return {"voice": voice, "plan": plan, "consent": profile["consent"]}


def sample(client, voice, text, output):
    """A single explicit trial take; never overwrites an earlier one."""
    from .narrative import spoken
    output = Path(output)
    if output.exists():
        raise VoiceStudioError("voicestudio_sample_exists", str(output))
    live = live_voice(client, voice)
    output.parent.mkdir(parents=True, exist_ok=True)
    body = client.generate(request_fields(voice, spoken(text, voice.get("pronunciations", {}))))
    with output.open("xb") as stream:
        stream.write(body)
    return {"path": str(output), "bytes": len(body), "profile": live["profile_name"], "engine": voice["engine"],
            "settings": voice.get("settings", {}), "listening": "pending"}
