"""Agrège la veille du jour en chiffres pour la présentation (data/analyse-AAAA-MM-JJ.json).

Usage : python -I scripts/analyse.py [AAAA-MM-JJ]
Lit data/veille/<date>/summary.json et data/raw/sandbox_summary.json.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rate(vs, thr=2.0):
    return round(sum(1 for v in vs if v["outlier"] >= thr) / len(vs), 3) if vs else None


def med(xs):
    return round(statistics.median(xs), 2) if xs else None


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    s = json.loads((ROOT / "data" / "veille" / day / "summary.json").read_text(encoding="utf-8"))
    chans = s["channels"]
    pool = [v for c in chans if c["group"] != "self" for v in c["videos"] if v["outlier"]]
    out: dict = {"date": day, "n_channels": len(chans), "n_videos": len(pool), "base_rate": rate(pool)}

    # 1. Durée : taux de vidéos x2 par tranche, tous groupes puis talk-shows seuls.
    bins = [(0, 8), (8, 15), (15, 25), (25, 40), (40, 70), (70, 999)]
    def dur_table(vs):
        rows = []
        for lo, hi in bins:
            b = [v for v in vs if v["duration"] and lo * 60 <= v["duration"] < hi * 60]
            rows.append({"bin": f"{lo}-{hi}" if hi < 999 else f"{lo}+", "n": len(b), "rate2": rate(b), "median_outlier": med([v["outlier"] for v in b])})
        return rows
    out["duration_all"] = dur_table(pool)
    out["duration_creators"] = dur_table([v for v in pool if v["group"] == "top20"])
    out["duration_talkshows"] = dur_table([v for v in pool if v["group"] == "podcasts_us" or v["handle"] in ("Underscore_", "nicolasguyon", "lescastcodeurs", "ifthisthendev", "mattstefani")])

    # 2. Titres : taux x2 avec / sans chaque caractéristique.
    feats = ["question", "number", "caps_word", "hook_word", "first_person", "you", "pipe_or_colon"]
    out["title_features"] = []
    for f in feats:
        yes = [v for v in pool if v["features"][f]]
        no = [v for v in pool if not v["features"][f]]
        out["title_features"].append({"feature": f, "n_yes": len(yes), "rate_yes": rate(yes), "rate_no": rate(no)})
    lbins = [(0, 40), (40, 55), (55, 70), (70, 90), (90, 300)]
    out["title_length"] = []
    for lo, hi in lbins:
        b = [v for v in pool if lo <= v["features"]["length"] < hi]
        out["title_length"].append({"bin": f"{lo}-{hi}" if hi < 300 else f"{lo}+", "n": len(b), "rate2": rate(b)})

    # 3. Thèmes.
    topics = sorted({t for v in pool for t in v["features"]["topics"]})
    out["topics"] = []
    for t in topics:
        b = [v for v in pool if t in v["features"]["topics"]]
        if len(b) >= 8:
            out["topics"].append({"topic": t, "n": len(b), "rate2": rate(b), "median_outlier": med([v["outlier"] for v in b])})
    out["topics"].sort(key=lambda r: -r["rate2"])

    # 4. Repères par groupe et par chaîne.
    out["channels"] = [{k: c[k] for k in ("name", "handle", "group", "followers", "median_views", "median_duration_min", "uploads_per_week", "uploads_last_30d")} for c in chans]
    out["groups"] = {}
    for g in ("top20", "podcasts_us", "fr"):
        cs = [c for c in chans if c["group"] == g and c["median_views"]]
        out["groups"][g] = {
            "n": len(cs),
            "median_of_median_views": med([c["median_views"] for c in cs]),
            "median_duration_min": med([c["median_duration_min"] for c in cs if c["median_duration_min"]]),
            "median_uploads_per_week": med([c["uploads_per_week"] for c in cs if c["uploads_per_week"]]),
        }

    # 5. Meilleurs outliers récents (30 j) et de tout l'échantillon, hors SANDBOX.
    keep = ("title", "channel", "group", "views", "outlier", "age_days", "duration", "url", "id")
    recent = [v for v in pool if v["age_days"] is not None and v["age_days"] <= 30]
    out["top_recent"] = [{k: v[k] for k in keep} for v in sorted(recent, key=lambda v: -v["outlier"])[:40]]
    fr = [v for v in pool if v["group"] == "fr"]
    out["top_fr"] = [{k: v[k] for k in keep} for v in sorted(fr, key=lambda v: -v["outlier"])[:25]]

    # 6. SANDBOX en détail (métadonnées complètes de chaque vidéo).
    sb_path = ROOT / "data" / "raw" / "sandbox_summary.json"
    if sb_path.exists():
        sb = json.loads(sb_path.read_text(encoding="utf-8"))
        longs = [r for r in sb if r["dur"] > 180]
        shorts = [r for r in sb if r["dur"] <= 180]
        out["sandbox"] = {
            "followers": next((c["followers"] for c in chans if c["group"] == "self"), None),
            "long": longs,
            "shorts": shorts,
            "long_views_total": sum(r["views"] or 0 for r in longs),
            "short_views_total": sum(r["views"] or 0 for r in shorts),
            "long_median": med([r["views"] or 0 for r in longs]),
            "short_median": med([r["views"] or 0 for r in shorts]),
        }

    path = ROOT / "data" / f"analyse-{day}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("base_rate", "duration_all", "duration_creators", "duration_talkshows", "title_features", "title_length", "topics", "groups")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
