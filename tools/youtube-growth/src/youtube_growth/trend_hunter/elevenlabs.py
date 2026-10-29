"""Explicit included-credit generation; manual import remains the default."""
from __future__ import annotations

import base64
import json
import math
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import uuid4

from .core import write_json
from .production import check_pack, import_voice


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise ValueError("Redirection ElevenLabs refusée.")


def generate(directory, cfg, *, included_credits_only=False, opener=None):
    check_pack(directory)
    options = cfg["elevenlabs"]
    if not options["enabled"] or not included_credits_only:
        raise ValueError("Activer ElevenLabs dans la config locale et demander explicitement --included-credits-only, ou importer le MP3 manuellement.")
    secret = os.environ.get("ELEVENLABS_API_KEY")
    voice = options["voice_id"]
    if not secret or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", voice or ""):
        raise ValueError("Clé ElevenLabs et identifiant de voix requis.")
    directory = Path(directory)
    text = " ".join((directory / "script.md").read_text(encoding="utf-8").split())
    if len(text) > options["max_characters"]:
        raise ValueError("Script au-delà du plafond local ElevenLabs.")
    opener = opener or build_opener(NoRedirect()).open

    def call(path, body=None):
        request = Request("https://api.elevenlabs.io/v1/"+path, headers={"xi-api-key": secret, "Content-Type": "application/json"},
                          data=json.dumps(body).encode() if body else None, method="POST" if body else "GET")
        try:
            with opener(request, timeout=60) as response:
                raw = response.read(40_000_001)
            if len(raw) > 40_000_000:
                raise ValueError("Réponse ElevenLabs trop volumineuse.")
            return json.loads(raw)
        except (HTTPError, URLError, TimeoutError, OSError):
            raise RuntimeError("ElevenLabs indisponible ou accès refusé. Aucun endpoint alternatif ni nouvelle tentative automatique.") from None

    subscription = call("user/subscription")
    if subscription.get("allowed_to_extend_character_limit") is not False:
        raise ValueError("Dépassement ElevenLabs autorisé ou état inconnu : génération bloquée. Désactiver la facturation de dépassement dans le compte ou importer manuellement.")
    used, limit = subscription.get("character_count"), subscription.get("character_limit")
    if type(used) is not int or type(limit) is not int or limit-used < len(text) or subscription.get("status") != "active":
        raise ValueError("Crédits inclus insuffisants ou abonnement non vérifiable.")
    models = call("models")
    model = next((m for m in models if m.get("model_id") == options["model_id"]), None)
    if not model or model.get("can_do_text_to_speech") is not True or model.get("requires_alpha_access"):
        raise ValueError("Modèle non disponible pour la synthèse de cet abonnement.")
    rates = model.get("model_rates") or {}
    multiplier = rates.get("character_cost_multiplier")
    discount = rates.get("cost_discount_multiplier")
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (multiplier, discount)):
        raise ValueError("Coût du modèle non vérifiable ; importer la voix manuellement.")
    voice_info = call("voices/"+voice)
    # Shared voices may have custom credit multipliers. Limit automatic generation to stock voices.
    if voice_info.get("category") != "premade" or voice_info.get("sharing"):
        raise ValueError("Voix stock sans tarif personnalisé requise pour garantir le plafond ; importer les autres voix manuellement.")
    tiers = voice_info.get("available_for_tiers")
    if tiers and subscription.get("tier") not in tiers:
        raise ValueError("Voix non incluse dans cet abonnement.")
    maximum = model.get("maximum_text_length_per_request")
    credits = math.ceil(len(text)*multiplier*discount)
    if type(maximum) is not int or len(text) > maximum or limit-used < credits:
        raise ValueError("Limite de requête ou crédits inclus insuffisants.")
    attempt = directory / "audio" / "elevenlabs-attempt.json"
    if attempt.exists():
        raise ValueError("Une tentative ElevenLabs existe ; réconcilier son résultat avant toute nouvelle génération. L'import manuel reste disponible.")
    write_json(attempt, {"status": "started_result_unknown", "characters": len(text), "credits_upper_bound": credits, "model_id": options["model_id"],
                         "included_remaining_before": limit-used, "overage_disabled_observed": True})
    result = call("text-to-speech/"+voice+"/with-timestamps", {"text": text, "model_id": options["model_id"]})
    audio = directory / "audio" / ("elevenlabs-"+uuid4().hex[:12]+".mp3")
    with audio.open("xb") as stream:
        stream.write(base64.b64decode(result["audio_base64"], validate=True))
    alignment = directory / "audio" / (audio.stem+"-alignment.json")
    write_json(alignment, result["alignment"])
    receipt = import_voice(directory, audio, alignment_path=alignment)
    write_json(attempt, {"status": "received", "path": receipt["path"], "characters": len(text), "model_id": options["model_id"], "included_remaining_before": limit-used})
    return receipt
