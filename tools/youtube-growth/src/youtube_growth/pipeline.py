from __future__ import annotations

import os
from pathlib import Path
from contextlib import nullcontext

from .storage import open_journal, remote_journal_configured, execute_once, exclusive_run

from .core import State, find_new_uploads
from .replies import generate_reply
from .thumbnails import fetch_and_render, thumbnail_url
from .youtube_api import channel_context, list_recent_comment_threads, post_reply, post_top_level_comment, top_level_comment_exists, upload_video_ids, videos_by_id


def _enabled(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "true" if default else "false").strip().lower() in {"1", "true", "yes", "on"}


def _template(text: str, video: dict, video_id: str) -> str:
    snippet = video.get("snippet", {})
    replacements = {
        "title": str(snippet.get("title", "")),
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }
    return text.format_map(replacements).strip()


def _description(video: dict) -> str:
    value = video.get("snippet", {}).get("description", "")
    return value if isinstance(value, str) else ""


def _write_summary(path: Path, entries: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "# Résultat de l'automatisation YouTube\n\n" + ("\n".join(f"- {entry}" for entry in entries) or "- Aucune nouvelle action.\n")
    path.write_text(content, encoding="utf-8")


def run_poll() -> int:
    execute_actions = _enabled("YOUTUBE_EXECUTE_ACTIONS")
    if execute_actions and not _enabled("YOUTUBE_INITIAL_REVIEW_CONFIRMED"):
        raise RuntimeError("Validez le premier pipeline avant d'activer YOUTUBE_INITIAL_REVIEW_CONFIRMED.")
    state_path = Path(os.environ.get("YOUTUBE_STATE_PATH", ".state/youtube-growth.json"))
    use_journal = execute_actions or remote_journal_configured()
    journal = open_journal(state_path.parent / "operations.sqlite3") if use_journal else None
    try:
        lock = journal.exclusive_poll() if remote_journal_configured() else (exclusive_run(state_path.parent) if execute_actions else nullcontext())
        with lock:
            state = journal.load_state() if remote_journal_configured() else State.load(state_path)
            save_state = journal.save_state if remote_journal_configured() else lambda value: value.save(state_path)
            return _run_poll(state, save_state, journal, execute_actions)
    finally:
        if journal is not None:
            journal.close()


def _run_poll(state: State, save_state, journal, execute_actions: bool) -> int:
    from .youtube_api import build_youtube_service
    output_dir = Path(os.environ.get("YOUTUBE_OUTPUT_DIR", "output"))
    summary_path = Path(os.environ.get("GITHUB_STEP_SUMMARY", "output/summary.md"))
    service = build_youtube_service()
    entries: list[str] = []
    if service is None:
        entries.append("OAuth YouTube absent : passage sans effet. Configurez le secret `YOUTUBE_OAUTH_TOKEN_JSON` après le déploiement.")
        _write_summary(summary_path, entries)
        return 0

    channel_id, uploads_playlist_id = channel_context(service)
    current_ids = upload_video_ids(service, uploads_playlist_id)
    if not current_ids:
        entries.append("La playlist des vidéos mises en ligne est vide.")
        _process_new_comments(service, channel_id, {}, state, entries, execute_actions=False)
        save_state(state)
        _write_summary(summary_path, entries)
        return 0

    if state.last_video_id is None:
        state.last_video_id = current_ids[0]
        _process_new_comments(service, channel_id, {}, state, entries, execute_actions=False)
        save_state(state)
        entries.append(f"Initialisation du curseur sur `{current_ids[0]}`. Les vidéos existantes ne sont pas retraitées.")
        _write_summary(summary_path, entries)
        return 0

    new_ids = find_new_uploads(current_ids, state.last_video_id)
    if new_ids is None:
        state.last_video_id = current_ids[0]
        save_state(state)
        entries.append("Le curseur précédent n'est plus dans les 50 dernières vidéos; réinitialisation sans rejouer l'historique.")
        _write_summary(summary_path, entries)
        return 0

    all_ids = list(dict.fromkeys([*state.pending_video_ids, *new_ids]))
    videos = videos_by_id(service, all_ids)
    pending: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for video_id in all_ids:
        video = videos.get(video_id)
        if not video:
            entries.append(f"`{video_id}` : métadonnées indisponibles, l'élément reste en attente.")
            pending.append(video_id)
            continue
        snippet = video.get("snippet", {})
        title = str(snippet.get("title", ""))
        status = video.get("status", {})
        if status.get("privacyStatus") != "public" or status.get("uploadStatus") not in {None, "processed"}:
            pending.append(video_id)
            continue

        url = thumbnail_url(snippet.get("thumbnails", {}))
        if url:
            try:
                candidates = fetch_and_render(url, title, output_dir / video_id, video_id)
                entries.append(f"`{video_id}` : 3 miniatures candidates — " + ", ".join(f"`{item.name}`" for item in candidates) + ".")
            except (OSError, ValueError, RuntimeError) as error:
                entries.append(f"`{video_id}` : génération des miniatures échouée ({type(error).__name__}); intervention requise.")
        else:
            entries.append(f"`{video_id}` : aucune miniature source retournée par l'API.")

        if video_id not in state.posted_episode_comments and _enabled("YOUTUBE_POST_EPISODE_COMMENT"):
            comment_template = os.environ.get(
                "YOUTUBE_EPISODE_COMMENT_TEMPLATE",
                "",
            )
            comment = _template(comment_template, video, video_id)
            if execute_actions and comment and not top_level_comment_exists(service, video_id, channel_id, comment):
                execute_once(journal, "episode_comment", {"channel_id": channel_id, "video_id": video_id},
                             {"channel_id": channel_id, "video_id": video_id, "text": comment},
                             lambda: post_top_level_comment(service, channel_id, video_id, comment))
                state.posted_episode_comments.append(video_id)
                entries.append(f"`{video_id}` : commentaire principal publié. Il doit être épinglé manuellement dans YouTube Studio.")
            elif execute_actions and comment:
                state.posted_episode_comments.append(video_id)
                entries.append(f"`{video_id}` : le commentaire principal existe déjà; aucun doublon publié.")
            else:
                entries.append(f"`{video_id}` : commentaire proposé, non publié (`YOUTUBE_EXECUTE_ACTIONS` désactivé).")

    if new_ids:
        state.last_video_id = new_ids[-1]
    state.pending_video_ids = pending
    _process_new_comments(service, channel_id, videos, state, entries, execute_actions, journal)
    save_state(state)
    _write_summary(summary_path, entries)
    return 0


def _process_new_comments(service, channel_id: str, videos: dict, state: State, entries: list[str], execute_actions: bool, journal=None) -> None:
    if not state.comments_baselined:
        threads = list_recent_comment_threads(service, channel_id)
        state.seen_comment_ids = [
            str(thread.get("snippet", {}).get("topLevelComment", {}).get("id", ""))
            for thread in threads
            if thread.get("snippet", {}).get("topLevelComment", {}).get("id")
        ][-1000:]
        state.comments_baselined = True
        entries.append("Curseur des commentaires initialisé; les commentaires déjà présents sont ignorés.")
        return
    if not _enabled("YOUTUBE_AUTO_REPLY"):
        entries.append("Réponses automatiques désactivées par configuration.")
        return
    if not execute_actions:
        entries.append("Mode lecture seule : aucun commentaire n'est transmis au fournisseur IA et aucune réponse n'est publiée.")
        return
    threads = list_recent_comment_threads(service, channel_id)
    thread_comments: list[tuple[str, dict]] = []
    own_comment_ids = set(state.posted_episode_comments)
    for thread in threads:
        thread_id = str(thread.get("id", ""))
        snippet = thread.get("snippet", {})
        top = snippet.get("topLevelComment", {})
        top_id = str(top.get("id", thread_id))
        comment_snippet = top.get("snippet", {})
        if not thread_id or top_id in state.seen_comment_ids or top_id in own_comment_ids:
            continue
        if not snippet.get("canReply", False) or int(snippet.get("totalReplyCount", 0)) > 0:
            state.seen_comment_ids.append(top_id)
            continue
        author_channel = comment_snippet.get("authorChannelId", {}).get("value")
        if author_channel == channel_id:
            state.seen_comment_ids.append(top_id)
            continue
        thread_comments.append((thread_id, thread))

    max_replies = max(0, min(5, int(os.environ.get("YOUTUBE_MAX_REPLIES_PER_RUN", "1"))))
    for thread_id, thread in reversed(thread_comments[:max_replies]):
        snippet = thread.get("snippet", {})
        top = snippet.get("topLevelComment", {})
        comment_snippet = top.get("snippet", {})
        video_id = str(snippet.get("videoId", ""))
        video = videos.get(video_id)
        if not video:
            video = videos_by_id(service, [video_id]).get(video_id, {}) if video_id else {}
        title = str(video.get("snippet", {}).get("title", ""))
        description = _description(video)
        text = str(comment_snippet.get("textOriginal", comment_snippet.get("textDisplay", "")))
        decision = generate_reply(text, title, description)
        top_id = str(top.get("id", thread_id))
        if decision.publish:
            if journal is None:
                raise RuntimeError("Journal requis avant de publier une réponse.")
            execute_once(journal, "comment_reply", {"channel_id": channel_id, "parent_id": top_id},
                         {"channel_id": channel_id, "parent_id": top_id, "text": decision.reply},
                         lambda: post_reply(service, top_id, decision.reply))
            entries.append(f"Commentaire `{top_id}` : réponse publiée.")
        else:
            entries.append(f"Commentaire `{top_id}` : transmis pour revue humaine ({decision.reason}).")
        state.seen_comment_ids.append(top_id)
    state.seen_comment_ids = list(dict.fromkeys(state.seen_comment_ids))[-1000:]
