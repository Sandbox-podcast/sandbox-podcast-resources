"""Small server-only ElevenLabs adapter. No retries on generation requests."""
from __future__ import annotations

import base64
from email import policy
from email.parser import BytesParser
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    """Safe error code only; never expose the provider body or credentials."""


class GenerationUnknown(ProviderError):
    pass


def composition_duration(plan):
    """Validate the documented plan shape and return its actual billed duration."""
    if not isinstance(plan, dict) or set(plan) != {"positive_global_styles", "negative_global_styles", "sections"}:
        raise ValueError("elevenlabs_composition_plan_invalid")
    def strings(value):
        return isinstance(value, list) and all(isinstance(s, str) for s in value)
    if not strings(plan["positive_global_styles"]) or not strings(plan["negative_global_styles"]):
        raise ValueError("elevenlabs_composition_plan_invalid")
    sections = plan["sections"]
    if not isinstance(sections, list) or not sections:
        raise ValueError("elevenlabs_composition_plan_invalid")
    total = 0
    for section in sections:
        if not isinstance(section, dict) or set(section) != {"section_name", "duration_ms", "positive_local_styles", "negative_local_styles", "lines"}:
            raise ValueError("elevenlabs_composition_plan_invalid")
        if (not isinstance(section["section_name"], str) or not section["section_name"].strip()
                or type(section["duration_ms"]) is not int or section["duration_ms"] <= 0
                or any(not strings(section[k]) for k in ("positive_local_styles", "negative_local_styles", "lines"))):
            raise ValueError("elevenlabs_composition_plan_invalid")
        total += section["duration_ms"]
    if not 3000 <= total <= 600000:
        raise ValueError("elevenlabs_composition_duration_invalid")
    return total / 1000


def parse_audio_response(body: bytes, content_type: str):
    """The music detailed endpoint returns MIME parts, not JSON base64."""
    if content_type.lower().startswith("multipart/"):
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body)
        audio, metadata = None, {}
        for part in message.iter_parts():
            payload = part.get_payload(decode=True)
            if part.get_content_type() == "application/json":
                metadata = json.loads(payload)
            elif part.get_content_type().startswith("audio/") or part.get_content_type() == "application/octet-stream":
                audio = payload
        if not audio:
            raise ProviderError("elevenlabs_audio_missing")
        return audio, metadata
    if "json" in content_type:
        value = json.loads(body)
        audio = base64.b64decode(value.pop("audio_base64", ""), validate=True)
        if not audio:
            raise ProviderError("elevenlabs_audio_missing")
        return audio, value
    if not body:
        raise ProviderError("elevenlabs_audio_missing")
    return body, {}


class ElevenLabsClient:
    BASE = "https://api.elevenlabs.io"

    def __init__(self, options=None, *, transport=None):
        self.options = options or {}
        self._key = os.environ.get(self.options.get("api_key_env", "ELEVENLABS_API_KEY"))
        if not self._key and transport is None:
            raise ProviderError("elevenlabs_api_key_missing")
        self.transport = transport
        self._capabilities = None

    def request(self, method, path, value=None):
        if not path.startswith("/v1/") and not path.startswith("/v2/"):
            raise ValueError("elevenlabs_endpoint_invalid")
        if self.transport:
            return self.transport(method, path, value)
        request = Request(self.BASE + path, method=method,
                          data=json.dumps(value).encode("utf-8") if value is not None else None,
                          headers={"xi-api-key": self._key, "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.options.get("timeout_seconds", 180)) as response:
                return response.read(), {k.lower(): v for k, v in response.headers.items()}
        except HTTPError as error:
            # A rejected 4xx is known; a 5xx might have been generated and billed.
            if method == "POST" and error.code >= 500:
                raise GenerationUnknown("elevenlabs_generation_unknown") from None
            raise ProviderError("elevenlabs_http_" + str(error.code)) from None
        except (TimeoutError, OSError, URLError):
            error = GenerationUnknown if method == "POST" else ProviderError
            raise error("elevenlabs_generation_unknown" if method == "POST" else "elevenlabs_connection_failed") from None

    def get_json(self, path):
        body, _ = self.request("GET", path)
        return json.loads(body)

    def capabilities(self):
        if self._capabilities is None:
            models = self.get_json("/v1/models")
            subscription = self.get_json("/v1/user/subscription")
            voices, token = [], None
            while True:
                page = self.get_json("/v2/voices?" + urlencode({"page_size": 100, **({"next_page_token": token} if token else {})}))
                voices.extend({"voice_id": v["voice_id"], "name": v.get("name"), "category": v.get("category")} for v in page.get("voices", []))
                token = page.get("next_page_token")
                if not page.get("has_more") or not token:
                    break
            # Never retain invoices, account identifiers or API key details.
            self._capabilities = {"models": models, "voices": voices,
                                  "subscription": {k: subscription.get(k) for k in ("tier", "status", "character_count", "character_limit")}}
        return self._capabilities

    def validate_voice(self, voice_id, model_id):
        capabilities = self.capabilities()
        if not any(v["voice_id"] == voice_id for v in capabilities["voices"]):
            raise ProviderError("elevenlabs_voice_unavailable")
        model = next((m for m in capabilities["models"] if m["model_id"] == model_id), None)
        if not model or model.get("can_do_text_to_speech") is not True:
            raise ProviderError("elevenlabs_model_unavailable")
        free = capabilities["subscription"].get("tier") == "free"
        limits = [model.get("maximum_text_length_per_request"), model.get("max_characters_request_free_user" if free else "max_characters_request_subscribed_user")]
        limits = [v for v in limits if isinstance(v, int) and v > 0]
        if not limits:
            raise ProviderError("elevenlabs_text_limit_unknown")
        return model, min(limits)

    def tts(self, text, voice_id, model_id, *, voice_settings=None, previous_text=None, next_text=None, pronunciation_dictionary_locators=None):
        model, limit = self.validate_voice(voice_id, model_id)
        if not text or len(text) > limit:
            raise ProviderError("elevenlabs_text_limit_exceeded")
        settings = dict(voice_settings or {})
        allowed = {"stability", "similarity_boost", "speed"}
        if model.get("can_use_style"):
            allowed.add("style")
        if model.get("can_use_speaker_boost"):
            allowed.add("use_speaker_boost")
        if set(settings) - allowed:
            raise ProviderError("elevenlabs_voice_setting_unsupported")
        value = {"text": text, "model_id": model_id, "voice_settings": settings}
        if previous_text:
            value["previous_text"] = previous_text
        if next_text:
            value["next_text"] = next_text
        if pronunciation_dictionary_locators:
            value["pronunciation_dictionary_locators"] = pronunciation_dictionary_locators
        return self.request("POST", "/v1/text-to-speech/" + quote(voice_id, safe="") + "/with-timestamps?output_format=mp3_44100_128", value)

    def dialogue(self, inputs, model_id="eleven_v3", *, pronunciation_dictionary_locators=None):
        if not inputs or len({i["voice_id"] for i in inputs}) > 10 or sum(len(i["text"]) for i in inputs) > 2000:
            raise ProviderError("elevenlabs_dialogue_limit_exceeded")
        for item in inputs:
            self.validate_voice(item["voice_id"], model_id)
        value = {"inputs": [{"text": i["text"], "voice_id": i["voice_id"]} for i in inputs], "model_id": model_id}
        if pronunciation_dictionary_locators:
            value["pronunciation_dictionary_locators"] = pronunciation_dictionary_locators
        return self.request("POST", "/v1/text-to-dialogue/with-timestamps?output_format=mp3_44100_128", value)

    def music(self, *, model_id, prompt=None, duration_seconds=None, composition_plan=None):
        if model_id not in {"music_v1", "music_v2", "music_v2_5"}:
            raise ProviderError("elevenlabs_music_model_unsupported")
        if bool(prompt) == bool(composition_plan):
            raise ValueError("music_prompt_or_plan_required")
        value = {"model_id": model_id}
        if prompt:
            if len(prompt) > 4100 or not 3 <= duration_seconds <= 600:
                raise ValueError("music_prompt_or_duration_invalid")
            value.update(prompt=prompt, music_length_ms=round(duration_seconds * 1000), force_instrumental=True)
        else:
            # Keep the exact composition plan schema; never mix prompt-only params.
            if duration_seconds is not None:
                raise ValueError("music_plan_duration_is_in_sections")
            composition_duration(composition_plan)
            value["composition_plan"] = composition_plan
        return self.request("POST", "/v1/music/detailed?output_format=mp3_44100_128", value)

    def sound_effect(self, text, duration_seconds, *, loop=False, model_id="eleven_text_to_sound_v2"):
        if model_id not in {"eleven_text_to_sound_v2", "eleven_text_to_sound_v3"}:
            raise ProviderError("elevenlabs_effect_model_unsupported")
        if not .5 <= duration_seconds <= 30:
            raise ValueError("sound_effect_duration_invalid")
        return self.request("POST", "/v1/sound-generation?output_format=mp3_44100_128",
                            {"text": text, "duration_seconds": duration_seconds, "loop": bool(loop), "model_id": model_id})

    def history(self, request_id):
        """Match a known request ID, never guess from a similar text."""
        page = self.get_json("/v1/history?page_size=100")
        while True:
            for item in page.get("history", []):
                if item.get("request_id") == request_id:
                    return item
            if not page.get("has_more") or not page.get("last_history_item_id"):
                return None
            page = self.get_json("/v1/history?" + urlencode({"page_size": 100, "start_after_history_item_id": page["last_history_item_id"]}))

    def history_audio(self, history_item_id):
        return self.request("GET", "/v1/history/" + quote(history_item_id, safe="") + "/audio")
