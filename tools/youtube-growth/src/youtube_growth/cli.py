from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

from .identity import FIRST_VIDEO_ID, expected_channel_id, verify_video
from .storage import open_journal, exclusive_run, save_json


def doctor(token_path: Path) -> dict:
    return {"expected_channel_id": expected_channel_id(), "oauth_present": bool(os.environ.get("YOUTUBE_OAUTH_TOKEN_JSON", "").strip()) or token_path.is_file(),
            "dependencies": {name: importlib.util.find_spec(name) is not None for name in ("googleapiclient", "google_auth_oauthlib", "PIL", "requests")},
            "ffmpeg": bool(shutil.which("ffmpeg")), "ffprobe": bool(shutil.which("ffprobe")),
            "mode": "dry_run", "native_shorts": "Studio : Extraits et Shorts, selon éligibilité; mobile : Remix, Convertir en Short (60 secondes). Aucune API publique de conversion.",
            "connection": "not_verified", "note": "Ce diagnostic local n'authentifie pas la chaîne. Lancez audit après OAuth."}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilotage du SANDBOX YouTube Growth Agent")
    parser.add_argument("--token", type=Path, default=Path(os.environ.get("YOUTUBE_LOCAL_TOKEN_PATH", ".local/youtube-token.json")))
    parser.add_argument("--state-dir", type=Path, default=Path(".local/growth"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Vérifie les prérequis sans afficher de secret")
    audit = commands.add_parser("audit", help="Collecte Data API et Analytics après vérification d'identité")
    audit.add_argument("--video-id", default=FIRST_VIDEO_ID)
    audit.add_argument("--start", type=date.fromisoformat)
    audit.add_argument("--end", type=date.fromisoformat)
    plan = commands.add_parser("plan", help="Sauvegarde un plan de métadonnées depuis la vidéo réelle")
    plan.add_argument("--video-id", default=FIRST_VIDEO_ID)
    plan.add_argument("--patch", type=Path, required=True)
    apply = commands.add_parser("apply", help="Simule ou applique un plan relu")
    apply.add_argument("plan", type=Path)
    apply.add_argument("--execute", action="store_true")
    restore = commands.add_parser("restore", help="Simule ou restaure les métadonnées d'une sauvegarde")
    restore.add_argument("backup", type=Path)
    restore.add_argument("--execute", action="store_true")
    commands.add_parser("status", help="Affiche les opérations réalisées ou à vérifier")
    native = commands.add_parser("native-pack", help="Prépare les extraits pour les outils YouTube, sans master")
    native.add_argument("--transcript", required=True, type=Path)
    native.add_argument("--spec", required=True, type=Path)
    native.add_argument("--video-id", default=FIRST_VIDEO_ID)
    native.add_argument("--duration", required=True, type=float)
    native.add_argument("--first", required=True, type=datetime.fromisoformat)
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            result = doctor(args.token)
            save_json(args.state_dir / "doctor.json", result)
        elif args.command == "status":
            journal = open_journal(args.state_dir / "operations.sqlite3")
            try:
                result = journal.entries()
            finally:
                journal.close()
        elif args.command == "native-pack":
            from .editorial import parse_youtube_transcript, prepare_native_pack, save_native_pack
            transcript = parse_youtube_transcript(args.transcript.read_text(encoding="utf-8-sig"), args.video_id, args.duration)
            result = prepare_native_pack(transcript, _json(args.spec), args.video_id, args.duration, args.first)
            with exclusive_run(args.state_dir):
                save_native_pack(result, args.state_dir)
            result = {"status": "prepared", "path": str(args.state_dir / "native-pack.md"), "candidates": len(result["candidates"]), "created_on_youtube": 0}
        else:
            from .youtube_api import build_youtube_service
            service = build_youtube_service(args.token)
            if service is None:
                raise RuntimeError("OAuth absent. Lancez youtube_growth.auth avec un client Google Desktop; aucun audit API ni changement distant exécuté.")
            with exclusive_run(args.state_dir):
                if args.command == "audit":
                    from .audit import collect_audit, save_audit
                    from .youtube_api import build_analytics_service
                    result = collect_audit(service, build_analytics_service(args.token), args.video_id, args.start, args.end)
                    directory = args.state_dir / "audits" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                    save_audit(result, directory)
                    result = {"status": "collected", "identity_verified": True, "path": str(directory / "audit.md")}
                elif args.command == "plan":
                    from .operations import make_plan
                    result = make_plan(verify_video(service, args.video_id), _json(args.patch))
                    save_json(args.state_dir / "metadata-plan.json", result)
                else:
                    from .operations import execute_plan, restoration_plan
                    value = _json(args.backup if args.command == "restore" else args.plan)
                    result = execute_plan(service, restoration_plan(value) if args.command == "restore" else value, args.state_dir, args.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
