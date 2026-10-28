"""Entrée indépendante de Codex pour le Planificateur de tâches Windows."""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/youtube-growth/src"))

from youtube_growth.factory.contracts import load_config, iso, utcnow
from youtube_growth.factory.local_lock import local_lock
from youtube_growth.factory.runtime import run_once
from youtube_growth.factory.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/factory.json")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    config = load_config(args.config)
    directory = (args.state_dir or ROOT / config["state_directory"]).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("sandbox_factory")
    logger.setLevel(logging.INFO)
    logger.addHandler(RotatingFileHandler(directory / "worker.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"))
    try:
        with local_lock(directory / "worker-lock"):
            with Store(directory) as store:
                store.set_setting("runtime_service", {"entrypoint": str(Path(__file__).resolve()), "started_at": iso(utcnow()), "executable": sys.executable})
                for _ in range(args.limit):
                    result = run_once(store, config)
                    logger.info(json.dumps({"at": iso(utcnow()), **result}, ensure_ascii=False))
                    if result["status"] == "idle":
                        break
    except RuntimeError:
        logger.info(json.dumps({"at": iso(utcnow()), "status": "blocked_or_worker_already_active"}))
        return 1
    except Exception as error:
        logger.error(json.dumps({"at": iso(utcnow()), "error_type": type(error).__name__}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
