"""Run `python -m youtube_growth.factory --help` from the repository."""
from __future__ import annotations

import argparse
import copy
from datetime import timedelta
import json
import math
from pathlib import Path
import shutil
import sqlite3
import sys
import time

from .contracts import ROOT, digest, instant, iso, load_config, load_json, utcnow
from .store import Store
from . import runtime, scheduler


def parser():
    result = argparse.ArgumentParser(description="Factory SANDBOX persistante, simulation sociale uniquement.")
    result.add_argument("--config", type=Path, default=ROOT / "config/factory.json")
    result.add_argument("--state-dir", type=Path)
    result.add_argument("--now", help="Horloge contrôlée ISO avec décalage, réservée à la recette en simulation.")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    prepare = commands.add_parser("prepare", help="Préparer localement un master jusqu'aux miniatures et au calendrier, sans diffusion.")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("--episode-id", required=True)
    prepare.add_argument("--title", required=True)
    prepare.add_argument("--publication-at")
    prepare.add_argument("--next-filming-at")
    prepare.add_argument("--transcript", type=Path)
    prepare.add_argument("--full-episode-url")
    prepare.add_argument("--full-episode-id")
    prepare.add_argument("--enqueue-only", action="store_true")
    prepare.add_argument("--limit", type=int, default=2000)
    prepare.add_argument("--synthetic", action="store_true", help="Identifier un master fabriqué pour une recette.")
    revise = commands.add_parser("revise-local", help="Appliquer un plan de correction sourcé, file suspendue, sans supprimer de média.")
    revise.add_argument("plan", type=Path)
    for name in ("process", "plan"):
        command = commands.add_parser(name)
        command.add_argument("episode_id")
    render = commands.add_parser("render")
    render.add_argument("episode_id")
    render.add_argument("segment_id")
    render.add_argument("--format", choices=["vertical", "horizontal"], default="vertical")
    qa = commands.add_parser("qa")
    qa.add_argument("asset_id")
    qa.add_argument("--reviewer", required=True)
    qa.add_argument("--evidence", required=True)
    qa.add_argument("--checks", nargs="+", required=True, choices=["visual", "audio", "editorial", "subtitles"])
    thumbnails = commands.add_parser("thumbnails")
    thumbnails.add_argument("publication_id")
    thumbnails.add_argument("--brief", type=Path, required=True)
    thumbnail_review = commands.add_parser("review-thumbnails")
    thumbnail_review.add_argument("publication_id")
    thumbnail_review.add_argument("--reviewer", required=True)
    thumbnail_review.add_argument("--evidence", required=True)
    from .thumbnails import CHECKS
    thumbnail_review.add_argument("--checks", nargs="+", required=True, choices=sorted(CHECKS))
    for name in ("status", "diagnostics", "report", "brief"):
        command = commands.add_parser(name)
        command.add_argument("--episode-id")
        if name in {"status", "diagnostics"}:
            command.add_argument("--platform")
    for name in ("worker", "simulate"):
        command = commands.add_parser(name)
        command.add_argument("--once", action="store_true")
        command.add_argument("--limit", type=int, default=100)
        command.add_argument("--interval", type=float, default=15)
    commands.add_parser("watch")
    commands.add_parser("pause")
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("publication_id")
    reconcile.add_argument("--receipt", type=Path, required=True)
    source_review = commands.add_parser("reconcile-source")
    source_review.add_argument("episode_id")
    source_review.add_argument("--evidence", required=True)
    source_review.add_argument("--reviewer", required=True)
    resume = commands.add_parser("resume")
    resume.add_argument("--job-id")
    collect = commands.add_parser("collect")
    collect.add_argument("--fixture", action="store_true")
    backup = commands.add_parser("backup")
    backup.add_argument("destination", type=Path)
    backup.add_argument("--include-media", action="store_true")
    restore = commands.add_parser("restore")
    restore.add_argument("snapshot", type=Path)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--with-worker", action="store_true", help="Exécuter aussi la file locale pendant que le tableau reste ouvert")
    demo = commands.add_parser("demo")
    demo.add_argument("--fixture-dir", type=Path)
    record = commands.add_parser("record")
    record.add_argument("--kind", choices=["observation", "experiment", "cost", "decision", "manual_publication"], required=True)
    record.add_argument("file", type=Path)
    decision = commands.add_parser("decision")
    decision.add_argument("--changes", type=Path)
    decision.add_argument("--reason")
    decision.add_argument("--reevaluate-at")
    decision.add_argument("--observation-id", action="append", default=[])
    decision.add_argument("--apply", action="store_true")
    decision.add_argument("--reverse")
    editorial = commands.add_parser("editorial")
    editorial.add_argument("episode_id")
    news = commands.add_parser("opportunities")
    news.add_argument("feed", type=Path)
    for command in (editorial, news):
        command.add_argument("--judgments", type=Path)
        command.add_argument("--generate", action="store_true")
    discovery = commands.add_parser("discover")
    discovery.add_argument("episode_id")
    discovery.add_argument("--proposals", type=Path)
    discovery.add_argument("--generate", action="store_true")
    research = commands.add_parser("research")
    research.add_argument("dossier", type=Path)
    research_fetch = commands.add_parser("research-fetch")
    research_fetch.add_argument("manifest", type=Path)
    design = commands.add_parser("draft-story")
    design.add_argument("brief", type=Path)
    design.add_argument("--generate", action="store_true")
    storytelling = commands.add_parser("storytelling-frame", help="Enregistrer le cadrage d'une nouvelle histoire")
    storytelling.add_argument("brief", type=Path)
    story_run=commands.add_parser("storytelling-run")
    story_run.add_argument("story_id")
    story_run.add_argument("--queue",action="store_true")
    story_import=commands.add_parser("storytelling-script")
    story_import.add_argument("story_id")
    story_import.add_argument("file",type=Path)
    story_control=commands.add_parser("storytelling-control")
    story_control.add_argument("story_id")
    story_control.add_argument("action",choices=["pause","resume","cancel","approve","lock","unlock"])
    story_control.add_argument("--scene-id")
    onboarding = commands.add_parser("video-onboarding", help="Conduire l'onboarding d'une nouvelle vidéo et conserver ses réponses.")
    onboarding.add_argument("action", choices=["start", "show", "list", "answer", "propose", "choose", "voice", "frame", "record", "spoken-check"])
    onboarding.add_argument("target", nargs="?", help="Session, ou fichier de texte pour spoken-check.")
    onboarding.add_argument("--set", action="append", default=[], metavar="CHAMP=VALEUR")
    onboarding.add_argument("--accepted-recommendation", action="store_true", help="Les valeurs sont des recommandations acceptées par Lou.")
    onboarding.add_argument("--file", type=Path, help="Réponses, propositions ou résultat d'étape en JSON.")
    onboarding.add_argument("--brief", type=Path, help="storytelling-brief.json produit par le Trend Hunter.")
    onboarding.add_argument("--session-id")
    onboarding.add_argument("--proposal", type=int)
    onboarding.add_argument("--topic")
    onboarding.add_argument("--confirmation", help="Les mots par lesquels Lou a exprimé son choix.")
    onboarding.add_argument("--profile")
    onboarding.add_argument("--engine")
    onboarding.add_argument("--authorization")
    onboarding.add_argument("--instruct", help="Consigne d'interprétation, seulement pour un moteur qui l'applique.")
    onboarding.add_argument("--effect-preset")
    onboarding.add_argument("--sentence-pause", type=float, help="Silence entre deux phrases, en secondes.")
    onboarding.add_argument("--pronounce", action="append", default=[], metavar="TERME=PRONONCIATION")
    onboarding.add_argument("--stage")
    onboarding.add_argument("--artifact", action="append", default=[], type=Path)
    onboarding.add_argument("--skill", action="append", default=[])
    onboarding.add_argument("--check", action="append", default=[], metavar="ID=STATUT[:NOTE]")
    onboarding.add_argument("--summary", default="")
    onboarding.add_argument("--target-minutes", type=float)
    voicestudio = commands.add_parser("voicestudio", help="Lire les profils et réglages réellement disponibles dans Voice Studio.")
    voicestudio.add_argument("action", choices=["status", "profiles", "plan", "sample"])
    voicestudio.add_argument("--url")
    voicestudio.add_argument("--session", help="Session d'onboarding dont la voix choisie sert à l'essai.")
    voicestudio.add_argument("--text")
    voicestudio.add_argument("--output", type=Path)
    voicestudio.add_argument("--instruct", help="Consigne à comparer, seulement pour l'essai.")
    voicestudio.add_argument("--video-type", default="documentary", choices=["documentary", "explainer", "commentary", "fiction", "docufiction"])
    voicestudio.add_argument("--register", choices=["analytic", "dynamic"])
    voicestudio.add_argument("--engine")
    narrative = commands.add_parser("narrative")
    narrative.add_argument("story", type=Path)
    narrative.add_argument("--stage", choices=["all", "research", "script", "storyboard", "voice", "render", "metadata"], default="all")
    narrative.add_argument("--format", choices=["horizontal", "vertical"], default="horizontal")
    narrative.add_argument("--draft", action="store_true")
    narrative.add_argument("--queue", action="store_true")
    narrative_review = commands.add_parser("review-narrative")
    narrative_review.add_argument("record_id", help="story_id:revision depuis status")
    narrative_review.add_argument("--reviewer", required=True)
    narrative_review.add_argument("--evidence", required=True)
    narrative_review.add_argument("--checks", nargs="+", required=True, choices=["facts", "editorial", "visual", "audio", "subtitles", "packaging"])
    learn = commands.add_parser("learn")
    learn.add_argument("--contexts", type=Path)
    analytics_import = commands.add_parser("import-analytics")
    analytics_import.add_argument("audit", type=Path)
    analytics_import.add_argument("--fixture", action="store_true")
    return result


def doctor(store, config):
    from .local_models import settings
    local = settings(config)
    tools = {name: shutil.which(name) for name in ("ffmpeg", "ffprobe")}
    health = store.setting("heartbeat")
    return {"mode": config["mode"], "live_enabled": False, "python": sys.version.split()[0], "tools": tools,
            "database": str(store.path), "integrity_check": store.db.execute("PRAGMA integrity_check").fetchone()[0],
            "heartbeat": health, "runtime_executed": health is not None,
            "production_capabilities": {"editorial": "local_model_configured" if config.get("generation", {}).get("local_command") else "structured_agent_input_required",
                "narrative_renderer": "ffmpeg_and_pillow", "stock_system_voice": "Windows_System_Speech_or_imported_recordings",
                "elevenlabs": "browser_session_handoff_or_opt_in_api", "storytelling": "sources_script_audio_timeline_ffmpeg_exports",
                "human_content_validation": "required", "social_publication": "disabled"},
            "accounts": {k: {"configured": len(v), "real_connection_verified": False} for k, v in config["authorized_accounts"].items()},
            "skills": [{"name": x.parent.name, "path": str(x), "catalog_verification": "requires_host_catalog"} for x in (ROOT / ".agents/skills").glob("sandbox-*/SKILL.md")],
            "local_autonomy": {"configured": local.get("enabled", False), "social_transport": False,
                               "models": {k: local.get(k) for k in ("editorial_model", "review_model", "transcription_model")},
                               "model_availability": "checked_when_local_stage_starts"},
            "blockers": (["ffmpeg_or_ffprobe_missing"] if not all(tools.values()) else [])+["real_connectors_disabled"]+([] if local.get("enabled") else ["no_background_model_configured"]),
            "discovery_notice": "Emplacement canonique contrôlé ; consulter le catalogue fourni par Codex pour attester leur chargement."}


def restore_snapshot(snapshot: Path, directory: Path):
    from .backups import restore
    return restore(snapshot, directory)


def run_demo(directory: Path, config: dict, *, fixture_dir=None, now=None):
    from .media import create_fixture
    config = copy.deepcopy(config)
    for platform in config["authorized_accounts"]:
        config["authorized_accounts"][platform] = ["simulation:"+platform] if platform != "linkedin" else []
    config["inbox_directory"] = str(directory / "inbox")
    config_path = directory / "simulation-config.json"
    directory.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    source = create_fixture(fixture_dir or directory / "input")
    current = instant(now or utcnow()).replace(hour=6, minute=0, second=0, microsecond=0)
    manifest = {"version": 1, "episode_id": "synthetic-demo", "title": "Fixture synthétique de la factory",
                "source": source["source"], "source_sha256": source["source_sha256"], "transcript": source["transcript"], "evidence": source["evidence"],
                "planned_publication_at": iso(current), "next_filming_at": iso(current+timedelta(days=3)), "available_at": iso(current),
                "availability_checked_at": iso(current), "availability_evidence": "synthetic_fixture_not_a_real_youtube_video", "availability": "available",
                "full_episode_id": "AbCdEfGhI12", "full_episode_url": "https://www.youtube.com/watch?v=AbCdEfGhI12", "synthetic": True}
    path = directory / "synthetic-demo.ready.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with Store(directory) as store:
        receipts = [runtime.ingest(store, path, now=current), runtime.ingest(store, path, now=current)]
        for _ in range(20):
            step = runtime.run_once(store, config, now=current)
            if step["status"] == "idle":
                break
        for asset in store.records("asset", "synthetic-demo"):
            runtime.review(store, asset["asset_id"], reviewer="synthetic_test_harness", evidence="Recette technique sur mire et sinus synthétiques ; aucune revue de propos réels.", checks=["visual", "audio", "editorial", "subtitles"], fixture=True, now=current)
        from .thumbnails import fixture_brief, CHECKS
        for publication in store.publications("synthetic-demo"):
            asset = store.get("asset", publication["asset_id"])
            if publication["platform"] == "youtube" and asset["format"] == "horizontal" and publication["status"] not in scheduler.TERMINAL:
                candidate = store.get("candidate", publication["segment_id"])
                brief = fixture_brief(store.get("episode", "synthetic-demo"), candidate, asset, now=current)
                brief_path = directory / "synthetic-thumbnail-brief.json"
                brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
                runtime.prepare_thumbnails(store, config, publication["id"], brief_path, now=current)
                runtime.review_thumbnails(store, publication["id"], reviewer="synthetic_contract_verifier", evidence="Fixture technique du contrat ; aucune revue de miniature réelle ni performance.", checks=sorted(CHECKS), now=current)
        calendar = scheduler.plan(store, config, "synthetic-demo", now=current)
        planned = sorted(p["scheduled_at"] for p in store.publications() if p["status"] == "scheduled")
        for at in planned:
            for _ in range(20):
                if runtime.run_once(store, config, now=instant(at))["status"] == "idle":
                    break
        runtime.collect(store, config, now=current+timedelta(days=4), fixture=True)
        scheduler.close_cycles(store, config, now=current+timedelta(days=4))
        result = runtime.report(store, episode_id="synthetic-demo", now=current+timedelta(days=4))
        result.update(ingestion=receipts, calendar=calendar, config_path=str(config_path), database=str(store.path),
                      assets=store.records("asset"), jobs=store.jobs(), synthetic=True)
        (directory / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result


def video_onboarding(store, config, args, *, now=None):
    from . import video_onboarding as onboarding
    values = {}
    for item in args.set:
        key, separator, raw = item.partition("=")
        if not separator or not key.strip():
            raise ValueError("Forme CHAMP=VALEUR attendue pour --set.")
        # Only lists and objects are JSON; a text answer such as "2026" or "null" stays text.
        values[key.strip()] = json.loads(raw) if raw[:1] in ("[", "{") else raw
    payload = load_json(args.file) if args.file and args.action not in {"spoken-check"} else None
    action, target = args.action, args.target
    if action == "list":
        return {"sessions": onboarding.sessions(store)}
    if action == "spoken-check":
        if not target:
            raise ValueError("Fichier de texte ou de scénario requis.")
        return onboarding.spoken_report(onboarding._texts(Path(target)), target_seconds=args.target_minutes*60 if args.target_minutes else None)
    if action == "start":
        brief = load_json(args.brief) if args.brief else None
        return onboarding.start(store, answers={**(payload or {}), **values}, brief=brief, session_id=args.session_id or target, now=now)
    if not target:
        raise ValueError("Identifiant de session requis.")
    if action == "show":
        return onboarding.next_step(store, target)
    if action == "answer":
        origin = "accepted_recommendation" if args.accepted_recommendation else "user"
        return onboarding.answer(store, target, {**(payload or {}), **values}, origin=origin, now=now)
    if action == "propose":
        return onboarding.propose_topics(store, target, (payload or {}).get("proposals", payload), now=now)
    if action == "choose":
        return onboarding.choose_topic(store, target, rank=args.proposal, topic=args.topic, confirmation=args.confirmation, now=now)
    if action == "voice":
        from .voicestudio import DEFAULT_URL, VoiceStudio, discover
        found = discover(VoiceStudio(config.get("voicestudio", {}).get("base_url", DEFAULT_URL)))
        words = dict(item.split("=", 1) for item in args.pronounce if "=" in item) or None
        if len(words or {}) != len(args.pronounce):
            raise ValueError("Forme TERME=PRONONCIATION attendue pour --pronounce.")
        settings = {"instruct": args.instruct, "effect_preset": args.effect_preset, "pause_between_sentences_seconds": args.sentence_pause}
        return onboarding.choose_voice(store, target, found, profile_id=args.profile, engine=args.engine,
                                       authorization=args.authorization, confirmation=args.confirmation,
                                       settings=settings, pronunciations=words, now=now)
    if action == "frame":
        return onboarding.frame_story(store, target, now=now)
    data = payload or {}
    checks = dict(data.get("checks", {}))
    for item in args.check:
        key, _, rest = item.partition("=")
        status, _, note = rest.partition(":")
        checks[key] = {"status": status, **({"note": note} if note else {})}
    return onboarding.record_stage(store, target, args.stage or data.get("stage"),
                                   artifacts=[*data.get("artifacts", []), *map(str, args.artifact)],
                                   skills_used=[*data.get("skills_used", []), *args.skill], checks=checks,
                                   summary=args.summary or data.get("summary", ""), status=data.get("status", "complete"),
                                   reason=data.get("reason"), now=now)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        config = load_config(args.config)
        directory = (args.state_dir or ROOT / config["state_directory"]).resolve()
        now = instant(args.now) if args.now else None
        if args.command == "restore":
            result = restore_snapshot(args.snapshot.resolve(), directory)
        elif args.command == "demo":
            # Keep synthetic identities and performance out of the operational DB.
            target = args.state_dir.resolve() if args.state_dir else ROOT / ".local/factory-demo"
            if target == (ROOT / config["state_directory"]).resolve():
                raise ValueError("La recette exige une base distincte de la factory opérationnelle.")
            result = run_demo(target, config, fixture_dir=args.fixture_dir, now=now)
        elif args.command == "serve":
            from .web import serve
            serve(directory, config, port=args.port, with_worker=args.with_worker)
            return
        else:
            with Store(directory) as store:
                command = args.command
                if command == "doctor":
                    result = doctor(store, config)
                elif command in {"editorial", "opportunities"}:
                    from .editorial_runtime import assess
                    result = assess(store, config, episode_id=args.episode_id if command == "editorial" else None,
                                    feed=args.feed if command == "opportunities" else None, judgments_path=args.judgments,
                                    use_model=args.generate, now=now)
                elif command == "discover":
                    from .editorial_runtime import discover
                    result = discover(store, config, args.episode_id, proposals_path=args.proposals, use_model=args.generate, now=now)
                elif command == "research":
                    from .research import verify
                    result = verify(load_json(args.dossier), base=args.dossier.resolve().parent, now=now)
                    store.put("research", result["research_id"], result, now=now)
                elif command == "research-fetch":
                    from .research import fetch_sources
                    result = fetch_sources(load_json(args.manifest), store.directory/"research-sources", now=now)
                elif command == "draft-story":
                    from .editorial_runtime import draft_story
                    result = draft_story(store, config, args.brief, use_model=args.generate, now=now)
                elif command == "storytelling-frame":
                    from .storytelling import frame
                    result = frame(store, load_json(args.brief), now=now)
                elif command == "storytelling-run":
                    from .storytelling import enqueue, run
                    result=enqueue(store,args.story_id,now=now) if args.queue else run(store,config,args.story_id,now=now)
                elif command == "storytelling-script":
                    from .storytelling import import_script
                    result=import_script(store,args.story_id,load_json(args.file),now=now)
                elif command == "storytelling-control":
                    from .storytelling import control
                    result=control(store,args.story_id,args.action,scene_id=args.scene_id,now=now)
                elif command == "video-onboarding":
                    result = video_onboarding(store, config, args, now=now)
                elif command == "voicestudio":
                    from .voicestudio import DEFAULT_URL, VoiceStudio, check_compatibility, discover, interpretation_plan, sample
                    client = VoiceStudio(args.url or config.get("voicestudio", {}).get("base_url", DEFAULT_URL))
                    found = discover(client)
                    if args.action == "sample":
                        session = store.get("video_onboarding", args.session or "") or {}
                        voice = (session.get("voice") or {}).get("voice")
                        if not voice or not args.text or not args.output:
                            raise ValueError("Session avec une voix Voice Studio choisie, --text et --output requis.")
                        if args.instruct:
                            voice = {**voice, "settings": {**voice["settings"], "instruct": args.instruct}}
                            check_compatibility(voice, found.get("version", ""))
                        result = sample(client, voice, args.text, args.output)
                    elif args.action == "plan" and found["status"] == "available":
                        engine = args.engine or found["active_engine"]
                        result = interpretation_plan(args.video_type, engine, found["version"], register=args.register, presets=found["effect_presets"])
                    elif args.action == "profiles" and found["status"] == "available":
                        result = {k: found[k] for k in ("version", "active_engine", "profiles")}
                    else:
                        result = found
                elif command == "narrative":
                    from .narrative import run
                    from .media import fingerprint
                    if args.queue:
                        payload = {"story_path": str(args.story.resolve(strict=True)), "story_sha256": fingerprint(args.story),
                                   "stage": args.stage, "format": args.format, "draft": args.draft}
                        job_id = store.enqueue("narrative", load_json(args.story).get("episode_id"), payload, now=now)
                        result = {"status": "queued", "job_id": job_id}
                    else:
                        result = run(store, config, args.story, stage=args.stage, format_name=args.format, draft=args.draft, now=now)
                elif command == "review-narrative":
                    from .narrative import review
                    result = review(store, args.record_id, reviewer=args.reviewer, evidence=args.evidence, checks=args.checks, now=now)
                elif command == "learn":
                    from .analytics import compare_content
                    contexts = load_json(args.contexts).get("contents", []) if args.contexts else store.records("performance_context")
                    result = compare_content(store.records("observation"), contexts, now=now)
                    if args.contexts:
                        for context in contexts:
                            store.put("performance_context", context["entity_id"], context, now=now)
                elif command == "import-analytics":
                    from .analytics_import import import_audit
                    result = import_audit(store, config, load_json(args.audit), fixture=args.fixture, now=now)
                elif command == "ingest":
                    result = runtime.ingest(store, args.manifest, now=now)
                elif command == "revise-local":
                    from .local_revisions import apply_plan
                    result = apply_plan(store, config, args.plan, now=now)
                elif command == "prepare":
                    from .autonomy import prepare_master, run_key
                    if args.limit < 1:
                        raise ValueError("Le nombre maximal de passages du worker doit être positif.")
                    ingestion = prepare_master(store, config, args.source, episode_id=args.episode_id, title=args.title,
                        publication_at=args.publication_at, next_filming_at=args.next_filming_at, transcript=args.transcript,
                        full_episode_url=args.full_episode_url, full_episode_id=args.full_episode_id, synthetic=args.synthetic, now=now)
                    processed = 0
                    if not args.enqueue_only:
                        for _ in range(args.limit):
                            step = runtime.run_once(store, config, now=now)
                            if step["status"] == "idle":
                                break
                            processed += 1
                    episode = store.get("episode", args.episode_id)
                    result = {"mode": "local_only", "ingestion": ingestion, "processed_jobs": processed,
                              "run": store.get("local_run", run_key(episode, config)),
                              "calendar": store.get("local_calendar", args.episode_id)}
                elif command == "process":
                    result = runtime.process(store, config, args.episode_id, now=now)
                elif command == "render":
                    result = runtime.render_candidate(store, config, args.episode_id, args.segment_id, args.format, now=now)
                elif command == "qa":
                    result = runtime.review(store, args.asset_id, evidence=args.evidence, reviewer=args.reviewer, checks=args.checks, now=now)
                elif command == "thumbnails":
                    result = runtime.prepare_thumbnails(store, config, args.publication_id, args.brief, now=now)
                elif command == "review-thumbnails":
                    result = runtime.review_thumbnails(store, args.publication_id, reviewer=args.reviewer, evidence=args.evidence, checks=args.checks, now=now)
                elif command == "plan":
                    result = scheduler.plan(store, config, args.episode_id, now=now)
                elif command == "watch":
                    result = runtime.watch(store, config, now=now)
                elif command in {"worker", "simulate"}:
                    if args.limit < 1 or not math.isfinite(args.interval) or args.interval < 1:
                        raise ValueError("Limite et intervalle positifs requis.")
                    results = []
                    idle_count = 0
                    while True:
                        step = runtime.run_once(store, config, now=now)
                        results.append(step)
                        if args.once or command == "simulate" and (len(results) >= args.limit or step["status"] == "idle"):
                            break
                        if len(results) > 100:
                            results = results[-100:]
                        idle_count = idle_count+1 if step["status"] == "idle" else 0
                        if command == "simulate":
                            time.sleep(args.interval)
                        elif idle_count:
                            time.sleep(runtime.idle_delay(store, config, idle_count=idle_count, interval=args.interval, now=now))
                    result = {"mode": "simulation", "results": results}
                elif command in {"status", "diagnostics"}:
                    result = runtime.status(store, episode_id=args.episode_id, platform=args.platform)
                    if command == "diagnostics":
                        from .monitoring import enrich
                        result = enrich(store, result, config, now=now)
                elif command == "pause":
                    store.set_setting("paused", True)
                    store.event("queue_paused", None, {}, now=now)
                    result = {"paused": True}
                elif command == "reconcile":
                    from .connectors import build_connector
                    evidence = load_json(args.receipt)
                    with store.transaction():
                        row = store.publication(args.publication_id)
                        if not row or row["status"] != "unknown" or evidence.get("publication_id") != row["id"] or not evidence.get("evidence"):
                            raise ValueError("Publication inconnue au résultat incertain et preuve correspondante requises.")
                        if evidence.get("status") == "simulated":
                            connector = build_connector(row["platform"], row["account_id"], config)
                            receipt = connector.reconcile({**row, "publication_id": row["id"], "status": "simulated", "remote_id": evidence.get("remote_id")})
                            if receipt.get("status") != "simulated":
                                raise ValueError("L'identifiant simulé ne correspond pas à la publication.")
                            row.update(receipt, status="simulated", reconciliation_evidence=evidence["evidence"])
                            job_status = "completed"
                        elif evidence.get("status") == "not_sent":
                            row.update(status="blocked", blocked_reason="reconciled_not_sent_requires_explicit_retry", reconciliation_evidence=evidence["evidence"])
                            job_status = "blocked"
                        else:
                            raise ValueError("Preuve de simulation ou de non-envoi requise ; aucun statut réel accepté.")
                        store.save_publication(row, now=now)
                        store.db.execute("UPDATE jobs SET status=?,last_error=NULL WHERE id=? AND status='unknown'", (job_status, "dispatch:"+row["id"]))
                        store.event("publication_reconciled", row["id"], evidence, now=now)
                        result = row
                elif command == "reconcile-source":
                    with store.transaction():
                        episode = store.get("episode", args.episode_id)
                        if not episode or not args.evidence.strip() or not args.reviewer.strip():
                            raise ValueError("Épisode, responsable et preuve de rapprochement requis.")
                        if any(p["status"] in {"unknown", "sending"} for p in store.publications(args.episode_id)):
                            raise ValueError("Réconcilier d'abord les publications incertaines.")
                        episode["source_revision_requires_reconciliation"] = False
                        episode["source_reconciliation"] = {"source_sha256": episode["source_sha256"], "reviewer": args.reviewer, "evidence": args.evidence, "at": iso(now or utcnow())}
                        store.put("episode", args.episode_id, episode, episode_id=args.episode_id, now=now)
                        store.event("source_reconciled", args.episode_id, episode["source_reconciliation"], now=now)
                        result = {"status": "source_reconciled", "existing_publications_preserved": True, "episode_id": args.episode_id}
                elif command == "resume":
                    if args.job_id:
                        store.retry(args.job_id, now=now)
                    else:
                        store.set_setting("paused", False)
                        store.event("queue_resumed", None, {}, now=now)
                    result = {"paused": store.setting("paused", False), "job_id": args.job_id}
                elif command == "collect":
                    result = runtime.collect(store, config, now=now, fixture=args.fixture)
                elif command == "report":
                    result = runtime.report(store, episode_id=args.episode_id, now=now, config=config)
                elif command == "brief":
                    result = runtime.brief(store, config, episode_id=args.episode_id, now=now)
                elif command == "backup":
                    from .backups import backup
                    result = backup(store, args.destination, include_media=args.include_media)
                elif command == "record":
                    from .analytics import validate_observation, validate_experiment, budget_status, apply_decision
                    value = load_json(args.file)
                    field = {"observation": "observation_id", "experiment": "experiment_id", "cost": "cost_id", "decision": "decision_id"}.get(args.kind)
                    if args.kind == "observation":
                        validate_observation(value)
                    elif args.kind == "experiment":
                        validate_experiment(value)
                    elif args.kind == "cost":
                        budget_status(store.records("cost")+[value], {"currency": config["budgets"]["currency"], "episode_max": config["budgets"]["episode_limit"]})
                    elif args.kind == "decision":
                        apply_decision(config, value)
                    else:
                        row = store.publication(value["publication_id"])
                        if not row or row["platform"] != "linkedin" or not value.get("url", "").startswith("https://www.linkedin.com/") or not value.get("evidence"):
                            raise ValueError("Publication LinkedIn connue, URL et preuve requises.")
                        row.update(status="manual_confirmed", remote_url=value["url"], published_at=iso(value["published_at"]), manual_evidence=value["evidence"])
                        store.save_publication(row, now=now)
                        field = "publication_id"
                    previous = store.get(args.kind, value[field])
                    if previous and previous != value and args.kind in {"observation", "cost", "decision"}:
                        raise ValueError("Identifiant déjà importé avec une valeur différente ; conserver la provenance et créer une nouvelle observation.")
                    store.put(args.kind, value[field], value, episode_id=value.get("episode_id"), now=now)
                    store.event("record_imported", value[field], {"kind": args.kind}, now=now)
                    result = {"status": "imported", "kind": args.kind, "id": value[field]}
                elif command == "decision":
                    from .analytics import make_decision, apply_decision
                    if args.reverse:
                        decision = store.get("decision", args.reverse)
                        if not decision:
                            raise ValueError("Décision inconnue.")
                        updated = apply_decision(config, decision, reverse=True)
                    else:
                        if not all((args.changes, args.reason, args.reevaluate_at)):
                            raise ValueError("--changes, --reason et --reevaluate-at requis.")
                        evidence_rows = [store.get("observation", identity) for identity in args.observation_id]
                        if any(row is None for row in evidence_rows):
                            raise ValueError("Une observation citée est absente de la base.")
                        if args.apply and any(row.get("data_class") == "synthetic_fixture" for row in evidence_rows):
                            raise ValueError("Les mesures synthétiques permettent une proposition, pas une modification de configuration.")
                        decision = make_decision(config, load_json(args.changes), reason=args.reason, observation_ids=args.observation_id,
                                                 recorded_at=iso(now or utcnow()), reevaluate_at=args.reevaluate_at)
                        updated = apply_decision(config, decision)
                    store.put("decision", decision["decision_id"], decision, now=now)
                    if args.apply:
                        temporary = args.config.with_suffix(".json.tmp")
                        temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
                        load_config(temporary)
                        temporary.replace(args.config)
                        store.event("decision_reverted" if args.reverse else "decision_applied", decision["decision_id"], {"config_sha256": digest(updated)}, now=now)
                    result = {"decision": decision, "applied": args.apply}
                else:
                    raise ValueError("Commande inconnue.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == "prepare" and not args.enqueue_only and result["run"]["status"] != "completed":
            return 3
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        detail = {"detail": error.detail} if getattr(error, "detail", None) else {}
        print(json.dumps({"error_type": type(error).__name__, "error": str(error), **detail}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
