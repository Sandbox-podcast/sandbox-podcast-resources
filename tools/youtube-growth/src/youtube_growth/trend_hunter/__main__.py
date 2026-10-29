"""Run from the repository root: python -m youtube_growth.trend_hunter."""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import shutil
import sys

from ..factory.local_lock import local_lock
from .core import ROOT, config, instant, load_json, stamp
from .production import import_voice, latest_pack, prepare
from .runtime import analyze, demo
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(description="Veille YouTube gratuite, recherche et production locales SANDBOX.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--state-dir", type=Path)
    subs = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subs.add_parser("analyze", help="Collecter les sources puis produire Markdown et JSON.")
    analyze_parser.add_argument("--mode", choices=("general", "ai-tech"))
    subs.add_parser("general", help="Analyse grand public.")
    subs.add_parser("ai-tech", help="Analyse IA et tech.")
    subs.add_parser("demo", help="Démonstration synthétique isolée.")
    subs.add_parser("doctor", help="Vérifier les prérequis sans réseau.")
    for name in ("prepare", "voice", "render"):
        child = subs.add_parser(name)
        child.add_argument("rank", type=int)
        child.add_argument("--run", dest="run_id")
        if name == "prepare":
            child.add_argument("--editorial", type=Path)
        if name == "voice":
            group = child.add_mutually_exclusive_group(required=True)
            group.add_argument("--import", dest="import_path", type=Path)
            group.add_argument("--generate", action="store_true")
            child.add_argument("--alignment", type=Path)
            child.add_argument("--included-credits-only", action="store_true")
        if name == "render":
            child.add_argument("--allow-demo", action="store_true", help="Autoriser une courte fixture synthétique.")
    outcome = subs.add_parser("record-result", help="Conserver les performances d'une vidéo publiée manuellement.")
    outcome.add_argument("path", type=Path)
    subs.add_parser("results", help="Comparer les recommandations aux relevés manuels.")
    args = parser.parse_args(argv)
    cfg = config(args.config, args.command if args.command in {"general", "ai-tech"} else getattr(args, "mode", None))
    directory = args.state_dir or ROOT / (".local/youtube-trend-hunter-demo" if args.command == "demo" else ".local/youtube-trend-hunter")
    if args.command == "doctor":
        try:
            import PIL
            pillow = PIL.__version__
        except ImportError:
            pillow = None
        result = {"python": sys.version.split()[0], "pillow": pillow, "ffmpeg": bool(shutil.which("ffmpeg")), "ffprobe": bool(shutil.which("ffprobe")), "config": "valid", "network": "not_called"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if pillow and result["ffmpeg"] and result["ffprobe"] else 1
    with local_lock(directory):
        store = Store(directory)
        try:
            if args.command in {"analyze", "general", "ai-tech", "demo"}:
                # Keep demonstration evidence and recommendation suppression out of real analyses.
                existing = store.db.execute("SELECT body FROM runs LIMIT 1").fetchone()
                if existing and json.loads(existing[0])["synthetic"] != (args.command == "demo"):
                    raise ValueError("Utiliser un état distinct pour la démonstration et les données réelles.")
                report, path = demo(store, cfg) if args.command == "demo" else analyze(store, cfg)
                result = {"status": "demonstration" if report["synthetic"] else "analyzed", "count": len(report["opportunities"]), "report": str(path / "report.md"), "json": str(path / "report.json"), "run_id": report["run_id"], "source_status": report["source_status"]}
            elif args.command == "prepare":
                path = prepare(store, args.rank, cfg, run_id=args.run_id, editorial_path=args.editorial)
                result = {"directory": str(path), "status": load_json(path / "pack.json")["status"]}
            elif args.command in {"voice", "render"}:
                path = latest_pack(store, args.rank, args.run_id)
                if args.command == "render":
                    from .render import render
                    result = render(path, allow_demo=args.allow_demo)
                elif args.import_path:
                    result = import_voice(path, args.import_path, alignment_path=args.alignment)
                else:
                    from .elevenlabs import generate
                    result = generate(path, cfg, included_credits_only=args.included_credits_only)
            elif args.command == "record-result":
                row = load_json(args.path)
                required = {"run_id", "topic_id", "video_url", "published_at", "observed_at", "views", "evidence"}
                if not required <= row.keys() or type(row["views"]) is not int or row["views"] < 0:
                    raise ValueError("Relevé manuel incomplet ou vues invalides.")
                if instant(row["observed_at"]) < instant(row["published_at"]) or instant(row["observed_at"]) > instant(stamp()):
                    raise ValueError("Dates de relevé invalides.")
                report = store.run(row["run_id"])
                topic = next((r for r in report["opportunities"] if r["topic_id"] == row["topic_id"]), None)
                if not topic or not row["video_url"].startswith("https://www.youtube.com/watch?v=") or not row["evidence"].strip():
                    raise ValueError("Recommandation, URL YouTube et preuve requises.")
                row.update(recommendation_score=topic["score"], synthetic=report["synthetic"])
                with store.db:
                    store.db.execute("INSERT INTO outcomes(at,body) VALUES(?,?)", (stamp(), json.dumps(row, ensure_ascii=False)))
                result = {"status": "recorded", "notice": "Relevé manuel conservé ; aucune pondération modifiée automatiquement."}
            else:
                result = {"observations": [json.loads(r[0]) for r in store.db.execute("SELECT body FROM outcomes ORDER BY at")], "notice": "Comparer des vidéos de même format et au même âge. Aucun lien causal ni apprentissage automatique déduit."}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        finally:
            store.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, FileNotFoundError, KeyError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
