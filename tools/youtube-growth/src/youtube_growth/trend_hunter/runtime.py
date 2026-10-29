"""One repeatable collection; no scheduler, publication or generation API."""
from __future__ import annotations

from datetime import timedelta
import os
from uuid import uuid4
import xml.etree.ElementTree as ET

from .connectors import COLLECTORS, HTTP, YouTube
from .core import instant, signal, stamp
from .detection import assess, cluster, rank
from .reporting import save_report


def analyze(store, cfg, *, now=None, http=None):
    now = stamp(now)
    store.prune(now)
    http = http or HTTP(store, cfg, now)
    rows, status, samples, channels = [], {}, [], {}
    for name, collector in COLLECTORS.items():
        if not cfg["sources"][name]:
            status[name] = {"status": "disabled", "count": 0}
            continue
        try:
            found, errors = collector(http, cfg)
            rows.extend(found)
            status[name] = {"status": "partial" if errors else "ok", "count": len(found), "errors": errors}
        except (RuntimeError, ValueError, KeyError, TypeError, ET.ParseError) as error:
            status[name] = {"status": "unavailable", "count": 0, "errors": [str(error)]}
    if cfg["sources"]["youtube"] and os.environ.get("YOUTUBE_TREND_API_KEY"):
        youtube = YouTube(http, cfg, os.environ["YOUTUBE_TREND_API_KEY"])
        seed_groups = cluster(rows, cfg["topic_aliases"])
        assessed = [(g, assess(g, store, cfg, now, [])) for g in seed_groups]
        excluded = {"category_filtered", "outside_ai_tech", "production_too_complex"}
        assessed = [(g, a) for g, a in assessed if not excluded.intersection(a["rejection_reasons"])]
        seeds = [g["title"] for g, a in sorted(assessed, key=lambda pair: (-pair[1]["score"], -len(pair[1]["support_origins"]), pair[1]["topic_id"]))]
        found, errors = youtube.collect(seeds, store)
        rows.extend(found)
        samples, channels = youtube.search_samples, youtube.channels
        status["youtube"] = {"status": "partial" if errors else "ok", "count": len(found), "errors": errors}
    else:
        status["youtube"] = {"status": "no_key" if cfg["sources"]["youtube"] else "disabled", "count": 0,
                              "errors": ["Statistiques YouTube et concurrence indisponibles ; aucun scraping de secours."]}
    store.observe(rows)
    saved = [r for r in store.latest(instant(now)-timedelta(days=cfg["window_days"])) if not r.get("synthetic")]
    opportunities, rejected = rank(saved, store, cfg, now, samples)
    report = {"version": 1, "run_id": "run-"+uuid4().hex[:16], "collected_at": now, "mode": cfg["mode"],
              "synthetic": False, "requested_count": cfg["recommendations"], "opportunities": opportunities, "rejected": rejected,
              "source_status": status, "quota_usage": store.quotas(now), "http_requests": http.requests,
              "youtube_search_samples": samples, "channels": channels,
              "coverage_notice": "Le RSS Trends expose son instantané courant. Les fenêtres 24h/48h/7j filtrent les publications et l'historique local disponible ; elles ne reconstituent pas les tendances absentes avant la première collecte. Regroupement lexical, alias configurables ; la traduction et la vérification des faits demandent la lecture des sources dans le chat."}
    path = save_report(store, report)
    return report, path


def demo(store, cfg, *, now=None):
    now = stamp(now)
    published = stamp(instant(now)-timedelta(hours=12))
    rows = [signal("news", "Atelier IA : nouvel outil de schémas", "https://example.org/demo-a", published, now,
                   language="fr", region="FR", publisher_domain="example.org", synthetic=True),
            signal("hackernews", "Atelier IA : nouvel outil de schémas", "https://example.net/demo-b", published, now, language="en", metrics={"points": 120, "comments": 30}, synthetic=True)]
    store.observe(rows)
    selected, rejected = rank(rows, store, cfg, now, [])
    report = {"version": 1, "run_id": "demo-"+uuid4().hex[:16], "collected_at": now, "mode": cfg["mode"], "synthetic": True,
              "requested_count": cfg["recommendations"], "opportunities": selected, "rejected": rejected,
              "source_status": {"fixture": {"status": "synthetic", "count": len(rows)}}, "quota_usage": {},
              "coverage_notice": "Exemple fictif pour vérifier le parcours. Aucun sujet réel ni performance réelle.", "channels": {}, "youtube_search_samples": []}
    return report, save_report(store, report)
