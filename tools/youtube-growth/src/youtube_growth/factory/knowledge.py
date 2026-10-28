"""Dated editorial references; expiry prompts review rather than inventing updates."""
from __future__ import annotations

from .contracts import ROOT, instant, load_json


def knowledge_status(config, *, now):
    path = ROOT / config.get("knowledge", {}).get("registry", "docs/factory/youtube-knowledge.json")
    registry = load_json(path)
    if registry.get("version") != 1:
        raise ValueError("Version du registre de connaissances inconnue.")
    entries = []
    for entry in registry["entries"]:
        checked, review = instant(entry["checked_at"]), instant(entry["review_after"])
        if checked >= review or not entry.get("source_url", "").startswith("https://"):
            raise ValueError("Source datée et échéance de revue requises.")
        status = "future_reference" if checked > instant(now) else "review_due" if review <= instant(now) else "current_reference"
        entries.append({**entry, "status": status})
    return {"entries": entries, "review_required": any(e["status"] != "current_reference" for e in entries),
            "scope": "official_documentation_not_account_eligibility",
            "automatic_refresh": False}
