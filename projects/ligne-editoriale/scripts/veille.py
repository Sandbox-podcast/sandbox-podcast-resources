"""Veille YouTube SANDBOX : repère les vidéos qui surperforment sur les chaînes suivies.

Usage :
    python -I scripts/veille.py                      # toutes les chaînes, 30 dernières vidéos
    python -I scripts/veille.py --groups top20 fr    # seulement certains groupes
    python -I scripts/veille.py --n 50 --window 14   # plus d'historique, fenêtre de 14 jours

Sorties (dans le dossier du projet) :
    data/veille/AAAA-MM-JJ/raw/<handle>.json   relevé brut yt-dlp (cache du jour)
    data/veille/AAAA-MM-JJ/summary.json        chiffres par chaîne + toutes les vidéos scorées
    rapports/veille-AAAA-MM-JJ.md              le rapport à lire

Score d'outlier = vues de la vidéo / médiane des vues de la chaîne (vidéos de plus de 3 jours).
Un score de 3 veut dire « 3 fois mieux que d'habitude sur cette chaîne ». C'est ce chiffre qui
signale un sujet qui accroche, pas le nombre brut de vues.

Dépendances : Python 3.10+ et yt-dlp dans le PATH. Pas de clé d'API.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = Path(__file__).resolve().parent / "watchlist.json"

# Thèmes repérés dans les titres (anglais et français). Ordre = priorité d'affichage.
TOPICS = {
    "Claude / Anthropic": r"\bclaude\b|anthropic|\bopus\b|\bsonnet\b|\bhaiku\b|\bfable\b",
    "Claude Code / agents de code": r"claude code|\bcodex\b|cursor|opencode|copilot|windsurf|coding agent|agent de code",
    "OpenAI / ChatGPT": r"openai|chatgpt|\bgpt|sam altman|\bsora\b",
    "Google / Gemini": r"gemini|google|deepmind|\bveo\b",
    "Agents IA": r"\bagents?\b|agentic|agentique|openclaw|hermes|autonom",
    "Skills / MCP / workflows": r"\bskills?\b|\bmcp\b|workflow|n8n|automat",
    "Vibe coding / créer une app": r"vibe.?cod|build (an? )?(app|saas)|no.?code|lovable|bolt",
    "Emploi / métier de dev": r"\bjobs?\b|developers?|devs?\b|engineers?|développeu|métier|replace|remplac|fired|layoff|career|carrière|junior",
    "Argent / business": r"\$|€|money|million|billion|milliard|business|startup|revenue|make money|argent|income",
    "IA locale / hardware": r"\blocal\b|nvidia|\bgpu\b|mac studio|\bm[3-6]\b|rtx|hardware|open.?source|llama|qwen|deepseek|mistral",
    "Chine": r"china|chinese|chine|chinois|deepseek|qwen|kimi",
    "AGI / futur / risques": r"\bagi\b|superintelligen|singularit|danger|risk|risque|apocal|doom|conscious|conscien",
    "Comparatif / test de modèle": r"\bvs\.?\b|versus|compar|tested|i tested|je teste|benchmark|best model|meilleur modèle",
}

HOOK_WORDS = r"insane|crazy|shocking|finally|enfin|incroyable|fou\b|folle|dingue|warning|stop|never|jamais|dead|mort|killed|tue\b|end of|fin de|secret|truth|vérité|nobody|personne|everyone|tout le monde|changes everything|change tout|game.?changer|broke|cassé"


def run_ytdlp(url: str, n: int, lang: str) -> dict | None:
    cmd = [
        "yt-dlp", "--flat-playlist", "-J", "--no-warnings",
        "--playlist-end", str(n),
        "--extractor-args", "youtubetab:approximate_date",
        "--extractor-args", f"youtube:lang={lang}",
        "--add-headers", f"Accept-Language:{lang}",
        url,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=240, check=False)
    except subprocess.TimeoutExpired:
        return None
    if out.returncode != 0 or not out.stdout:
        return None
    return json.loads(out.stdout.decode("utf-8", errors="replace"))


def fetch_channel(ch: dict, n: int, raw_dir: Path) -> dict:
    cache = raw_dir / f"{ch['handle']}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    result = {"handle": ch["handle"], "entries": [], "followers": None, "errors": []}
    lang = ch.get("lang", "en")
    for tab in ch.get("tabs", ["videos"]):
        url = f"https://www.youtube.com/@{ch['handle']}/{tab}"
        # Les dates relatives (« 3 days ago ») et les abonnés ne sont lus par yt-dlp qu'en anglais.
        data = run_ytdlp(url, n, "en")
        if data is None:
            result["errors"].append(tab)
            continue
        # Les titres, eux, doivent venir dans la langue d'origine (YouTube traduit sinon).
        titles = {}
        if lang != "en":
            local = run_ytdlp(url, n, lang)
            if local:
                titles = {e["id"]: e.get("title") for e in local.get("entries") or [] if e and e.get("id")}
        result["followers"] = result["followers"] or data.get("channel_follower_count")
        for e in data.get("entries") or []:
            if not e or not e.get("id"):
                continue
            result["entries"].append({
                "id": e["id"],
                "title": titles.get(e["id"]) or e.get("title") or "",
                "duration": e.get("duration"),
                "views": e.get("view_count"),
                "timestamp": e.get("timestamp"),
                "tab": tab,
                "live": e.get("live_status"),
            })
    cache.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def title_features(title: str) -> dict:
    t = title.lower()
    return {
        "length": len(title),
        "words": len(title.split()),
        "question": "?" in title,
        "number": bool(re.search(r"\d", title)),
        "caps_word": bool(re.search(r"\b[A-Z]{3,}\b", re.sub(r"\b(AI|IA|GPT|LLM|MCP|API|AGI|CEO|CTO|SaaS|USA|PDF|RTX|GPU|CPU|IDE|SDK|UI|UX|FPS|OS)\b", "", title))),
        "hook_word": bool(re.search(HOOK_WORDS, t)),
        "first_person": bool(re.search(r"\b(i|i'm|my|me|we|our|je|j'|mon|ma|mes|on|nous)\b", t)),
        "you": bool(re.search(r"\b(you|your|tu|ton|ta|tes|vous|votre|vos)\b", t)),
        "pipe_or_colon": bool(re.search(r"[|:]", title)),
        "topics": [k for k, rx in TOPICS.items() if re.search(rx, t)],
    }


def score_channel(ch: dict, raw: dict, today: dt.date) -> dict:
    vids = []
    for e in raw["entries"]:
        if e["views"] is None:
            continue
        if e["duration"] is not None and e["duration"] < 61:
            continue  # on ne garde que le long format
        age = None
        if e["timestamp"]:
            age = max((today - dt.datetime.fromtimestamp(e["timestamp"], dt.timezone.utc).date()).days, 0)
        vids.append({**e, "age_days": age})
    mature = [v["views"] for v in vids if v["age_days"] is None or v["age_days"] >= 3]
    median = statistics.median(mature) if mature else None
    for v in vids:
        v["outlier"] = round(v["views"] / median, 2) if median else None
        v["views_per_day"] = round(v["views"] / max(v["age_days"] or 1, 1))
        v["features"] = title_features(v["title"])
        v["channel"] = ch["name"]
        v["handle"] = ch["handle"]
        v["group"] = ch["group"]
        v["url"] = f"https://www.youtube.com/watch?v={v['id']}"
    durations = [v["duration"] for v in vids if v["duration"]]
    ages = [v["age_days"] for v in vids if v["age_days"] is not None]
    last30 = [v for v in vids if v["age_days"] is not None and v["age_days"] <= 30]
    span = (max(ages) - min(ages)) if len(ages) > 1 else None
    per_week = round(len(ages) / (span / 7), 1) if span else None
    return {
        "handle": ch["handle"],
        "name": ch["name"],
        "group": ch["group"],
        "followers": raw.get("followers"),
        "errors": raw.get("errors", []),
        "n_videos": len(vids),
        "median_views": round(median) if median else None,
        "median_duration_min": round(statistics.median(durations) / 60, 1) if durations else None,
        "uploads_last_30d": len(last30),
        "uploads_per_week": per_week,
        "videos": vids,
    }


def fmt_n(x) -> str:
    if x is None:
        return "?"
    if x >= 1_000_000:
        return f"{x / 1_000_000:.1f} M".replace(".", ",")
    if x >= 1000:
        return f"{x / 1000:.0f} k"
    return str(x)


def fmt_dur(sec) -> str:
    if not sec:
        return "?"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def build_report(summary: dict, window: int) -> str:
    chans = summary["channels"]
    allv = [v for c in chans for v in c["videos"]]
    recent = [v for v in allv if v["age_days"] is not None and v["age_days"] <= window and v["outlier"]]
    hot = sorted([v for v in recent if v["outlier"] >= 2 and v["group"] != "self"], key=lambda v: -v["outlier"])
    young = sorted([v for v in allv if v["age_days"] is not None and v["age_days"] <= 5 and v["outlier"] and v["outlier"] >= 1.5 and v["group"] != "self"], key=lambda v: -v["views_per_day"])

    lines = [f"# Veille YouTube SANDBOX, {summary['date']}", ""]
    lines.append(f"{len(chans)} chaînes lues, {len(allv)} vidéos longues. Fenêtre des sujets chauds : {window} jours. Score = vues / médiane de la chaîne.")
    failed = [c["name"] for c in chans if c["errors"] and not c["videos"]]
    if failed:
        lines.append(f"Chaînes non lues ce jour : {', '.join(failed)}.")
    lines += ["", "## Sujets qui surperforment (score ≥ 2)", "", "| Score | Vues | Âge | Durée | Chaîne | Titre |", "|---:|---:|---:|---:|---|---|"]
    for v in hot[:30]:
        age = "≈1 mois" if v["age_days"] >= 30 else f"{v['age_days']} j"
        lines.append(f"| ×{v['outlier']:.1f} | {fmt_n(v['views'])} | {age} | {fmt_dur(v['duration'])} | {v['channel']} | [{v['title']}]({v['url']}) |")
    if not hot:
        lines.append("| | | | | | Aucune vidéo au-dessus de ×2 dans la fenêtre. |")

    lines += ["", "## En train de partir (moins de 5 jours, score ≥ 1,5)", ""]
    for v in young[:12]:
        lines.append(f"- ×{v['outlier']:.1f}, {fmt_n(v['views_per_day'])} vues/jour : **{v['title']}** ({v['channel']}, {v['age_days']} j) {v['url']}")
    if not young:
        lines.append("- Rien de notable.")

    # Thèmes : part des vidéos à score >= 2 qui contiennent le thème, comparée à la base.
    pool = [v for v in allv if v["outlier"] and v["group"] != "self"]
    lines += ["", "## Thèmes : taux de réussite", "", "Part des vidéos du thème qui font au moins ×2 la médiane de leur chaîne (toutes chaînes, 30 dernières vidéos).", "", "| Thème | Vidéos | Dont ×2+ | Taux |", "|---|---:|---:|---:|"]
    base_rate = sum(1 for v in pool if v["outlier"] >= 2) / max(len(pool), 1)
    rows = []
    for topic in TOPICS:
        tv = [v for v in pool if topic in v["features"]["topics"]]
        if len(tv) < 8:
            continue
        hits = sum(1 for v in tv if v["outlier"] >= 2)
        rows.append((hits / len(tv), topic, len(tv), hits))
    for rate, topic, n, hits in sorted(rows, reverse=True):
        lines.append(f"| {topic} | {n} | {hits} | {rate:.0%} |")
    lines.append(f"| *Base, toutes vidéos* | {len(pool)} | {sum(1 for v in pool if v['outlier'] >= 2)} | {base_rate:.0%} |")

    lines += ["", "## Chaînes", "", "| Chaîne | Groupe | Abonnés | Médiane vues | Durée médiane | Vidéos / sem. |", "|---|---|---:|---:|---:|---:|"]
    for c in sorted(chans, key=lambda c: -(c["median_views"] or 0)):
        lines.append(f"| {c['name']} | {c['group']} | {fmt_n(c['followers'])} | {fmt_n(c['median_views'])} | {c['median_duration_min'] or '?'} min | {c['uploads_per_week'] or '?'} |")

    lines += ["", "## Comment s'en servir", "",
              "1. Prendre les 3 premiers sujets du tableau qui passent le filtre SANDBOX (ça intéresse un dev, un PM ou un CTO ; on a un avis ou une expérience dessus).",
              "2. Les transformer en question de débat pour l'épisode (skill `sandbox-sujet`).",
              "3. Ne pas recopier le titre : reprendre la tension du sujet, pas la formulation.",
              ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=30, help="vidéos lues par chaîne et par onglet")
    ap.add_argument("--window", type=int, default=30, help="fenêtre en jours pour les sujets chauds")
    ap.add_argument("--groups", nargs="*", help="groupes à lire (top20, podcasts_us, fr, self)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    today = dt.date.today()
    channels = json.loads(WATCHLIST.read_text(encoding="utf-8"))["channels"]
    if args.groups:
        channels = [c for c in channels if c["group"] in args.groups]
    day_dir = ROOT / "data" / "veille" / today.isoformat()
    raw_dir = day_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(fetch_channel, c, args.n, raw_dir): c for c in channels}
        for f in as_completed(futs):
            c = futs[f]
            raw = f.result()
            results[c["handle"]] = score_channel(c, raw, today)
            status = "ERREUR " + ",".join(raw["errors"]) if raw["errors"] else "ok"
            print(f"{c['name']:<28} {len(raw['entries']):>3} vidéos  {status}", flush=True)

    summary = {"date": today.isoformat(), "n": args.n, "channels": [results[c["handle"]] for c in channels]}
    (day_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    report = build_report(summary, args.window)
    rep_dir = ROOT / "rapports"
    rep_dir.mkdir(exist_ok=True)
    out = rep_dir / f"veille-{today.isoformat()}.md"
    out.write_text(report, encoding="utf-8")
    print(f"\nRapport : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
