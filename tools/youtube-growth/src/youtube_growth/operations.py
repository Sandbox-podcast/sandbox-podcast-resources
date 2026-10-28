from __future__ import annotations

import copy
from pathlib import Path

from .identity import expected_channel_id, verify_video
from .storage import open_journal, remote_journal_configured, digest, now_iso, save_json


SNIPPET_FIELDS = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")
PATCH_FIELDS = {"title", "description", "tags"}


def writable_snippet(video: dict) -> dict:
    source = video.get("snippet", {})
    if not isinstance(source, dict) or not source.get("title") or not source.get("categoryId"):
        raise ValueError("Le titre et la catégorie d'origine sont nécessaires à une mise à jour.")
    return {key: copy.deepcopy(source[key]) for key in SNIPPET_FIELDS if key in source}


def validate_patch(value: object) -> dict:
    if not isinstance(value, dict) or not value or set(value) - PATCH_FIELDS:
        raise ValueError("Une optimisation peut modifier uniquement title, description et tags.")
    for key, item in value.items():
        if key == "tags":
            if not isinstance(item, list) or any(not isinstance(tag, str) or not tag.strip() or any(ord(c) < 32 for c in tag) for tag in item):
                raise ValueError("tags doit contenir des chaînes non vides.")
            # YouTube also counts quotes around tags containing spaces.
            if sum(len(tag) + (2 if " " in tag else 0) for tag in item) + max(0, len(item) - 1) > 500:
                raise ValueError("Les mots-clés dépassent la limite YouTube de 500 caractères.")
        elif not isinstance(item, str) or (key == "title" and (not item.strip() or len(item) > 100)) or (key == "description" and len(item.encode("utf-8")) > 5000):
            raise ValueError(f"{key} dépasse les contraintes YouTube.")
        elif "<" in item or ">" in item or any(ord(c) < 32 and c not in "\n\t" for c in item):
            raise ValueError(f"{key} contient des caractères interdits.")
    return copy.deepcopy(value)


def make_plan(video: dict, patch: object) -> dict:
    before = writable_snippet(video)
    after = {**before, **validate_patch(patch)}
    if video.get("snippet", {}).get("channelId") != expected_channel_id():
        raise ValueError("Impossible de préparer une modification pour une autre chaîne.")
    return {"version": 1, "channel_id": expected_channel_id(), "video_id": video["id"], "before": before, "after": after, "created_at": now_iso()}


def execute_plan(service, plan: dict, directory: Path, execute: bool = False) -> dict:
    if execute:
        from .factory.connectors import guard_legacy_write
        guard_legacy_write("youtube.metadata_or_restore")
    if not isinstance(plan, dict) or plan.get("channel_id") != expected_channel_id() or plan.get("version") != 1:
        raise ValueError("Plan non conforme ou destiné à une autre chaîne.")
    video = verify_video(service, plan["video_id"])
    current = writable_snippet(video)
    after = plan.get("after")
    before = plan.get("before")
    if not isinstance(after, dict) or not isinstance(before, dict) or set(after) - set(SNIPPET_FIELDS):
        raise ValueError("Le plan contient des propriétés non modifiables.")
    patch = {key: value for key, value in after.items() if key in PATCH_FIELDS}
    expected_after = {**before, **validate_patch(patch)}
    if after != expected_after:
        raise ValueError("La catégorie et les langues doivent rester identiques à la sauvegarde.")
    revision = plan.get("created_at")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("Le plan doit porter sa révision de préparation.")
    payload = {"channel_id": plan["channel_id"], "video_id": plan["video_id"], "before": before, "after": after, "revision": revision}
    if current == after:
        result = {"status": "already_applied", "video_id": video["id"]}
        if execute and (remote_journal_configured() or (directory / "operations.sqlite3").is_file()):
            journal = open_journal(directory / "operations.sqlite3")
            try:
                journal.finish(digest({"kind": "video_metadata", "payload": payload}), result)
            finally:
                journal.close()
        return result
    if current != before:
        raise RuntimeError("Les métadonnées ont changé depuis la préparation. Refaites le plan pour préserver ces changements.")
    if not execute:
        return {"status": "dry_run", "video_id": video["id"], "before": current, "after": after}
    save_json(directory / "backups" / f"{digest(payload)}.json", plan)
    journal = open_journal(directory / "operations.sqlite3")
    try:
        operation_id, should_execute = journal.begin("video_metadata", payload)
        if not should_execute:
            raise RuntimeError("Ce plan a déjà été exécuté. Préparez un nouveau plan après toute restauration.")
        # No automatic retry: a network timeout may follow a successful mutation.
        service.videos().update(part="snippet", body={"id": video["id"], "snippet": after}).execute()
        checked = verify_video(service, video["id"])
        if writable_snippet(checked) != after:
            raise RuntimeError("YouTube ne confirme pas les nouvelles métadonnées. Vérification manuelle requise.")
        result = {"status": "applied", "video_id": video["id"], "operation_id": operation_id}
        journal.finish(operation_id, result)
        return result
    finally:
        journal.close()


def restoration_plan(backup: dict) -> dict:
    return {**backup, "before": copy.deepcopy(backup["after"]), "after": copy.deepcopy(backup["before"]), "created_at": now_iso()}
