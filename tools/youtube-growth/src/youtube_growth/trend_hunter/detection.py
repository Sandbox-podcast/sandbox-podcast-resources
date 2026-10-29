"""Transparent heuristics: incomplete samples stay incomplete."""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
import math
from statistics import median
from urllib.parse import urlparse

from .core import instant, key, plain, tokens

TECH = {"ai", "ia", "intelligence", "openai", "anthropic", "claude", "codex", "gpt", "llm", "nvidia", "robot", "robotics", "robotique", "software", "logiciel", "technologie", "technology", "tech", "github", "google", "microsoft", "apple", "innovation", "quantum", "semiconductor", "puce", "numerique", "chatgpt", "gemini"}
SENSITIVE = {"suicide", "murder", "meurtre", "massacre", "killed", "mort", "deces", "attentat", "cancer", "treatment", "traitement", "investir", "stock", "election", "trump", "biden", "macron", "guerre", "war", "tragedy", "tragedie"}
COMPLEX = {"interview", "tournage", "benchmark", "review", "hands-on", "essai", "unboxing", "test-drive"}


def cluster(rows, aliases):
    groups = []
    for row in sorted(rows, key=lambda r: (r["published_at"] or r["observed_at"], r["id"]), reverse=True):
        words = tokens(row["title"])
        if not words:
            continue
        canonical = next((name for name, variants in aliases.items() if any(plain(v) in plain(row["title"]) for v in [name, *variants])), None)
        match = None
        for group in groups:
            if canonical and canonical == group["alias"]:
                match = group
                break
            shared = words & group["tokens"]
            union = words | group["tokens"]
            if not canonical and not group["alias"] and (words == group["tokens"] or len(shared) >= 2 and len(shared)/len(union) >= .4):
                match = group
                break
        if match:
            match["signals"].append(row)
        else:
            groups.append({"alias": canonical, "title": canonical or row["title"], "tokens": words, "signals": [row]})
    return groups


def video_metrics(row, store, cfg):
    views = row["metrics"].get("views")
    age = (instant(row["observed_at"])-instant(row["published_at"])).total_seconds()/3600 if row.get("published_at") else None
    result = {"video_id": row["video_id"], "format": row["format"], "age_hours": round(age, 2) if age is not None else None,
              "average_views_per_hour": views/age if views is not None and age and age > 0 else None,
              "interval_views_per_hour": None, "acceleration_ratio": None, "outperformance_ratio": None,
              "baseline_median": None, "baseline_count": 0, "baseline_method": "insufficient_comparable_history", "baseline_ids": []}
    history = [r for r in store.history(row["id"]) if r["metrics"].get("views") is not None and instant(r["observed_at"]) <= instant(row["observed_at"])]
    spaced = []
    for sample in reversed(history):
        if not spaced or (instant(spaced[-1]["observed_at"])-instant(sample["observed_at"])).total_seconds() >= 300:
            spaced.append(sample)
        if len(spaced) == 3:
            break
    rates = []
    for newer, older in zip(spaced, spaced[1:]):
        delta = newer["metrics"]["views"]-older["metrics"]["views"]
        hours = (instant(newer["observed_at"])-instant(older["observed_at"])).total_seconds()/3600
        if delta < 0:
            break
        rates.append(delta/hours)
    if rates:
        result["interval_views_per_hour"] = rates[0]
    if len(rates) == 2 and rates[1] > 0:
        result["acceleration_ratio"] = rates[0]/rates[1]
    if views is None or not age or age < .25 or row["format"] != "long":
        return result
    matches = []
    for other in store.baseline(row["channel_id"], row["id"], row["observed_at"]):
        if other.get("format") != row["format"]:
            continue
        eligible = []
        for sample in store.history(other["id"]):
            if not sample.get("published_at") or sample["metrics"].get("views") is None:
                continue
            other_age = (instant(sample["observed_at"])-instant(sample["published_at"])).total_seconds()/3600
            if instant(sample["observed_at"]) <= instant(row["observed_at"]) and abs(other_age-age) <= max(.25, age*.35):
                eligible.append((abs(other_age-age), sample))
        if eligible:
            chosen = min(eligible, key=lambda p: p[0])[1]
            matches.append((chosen["video_id"], chosen["metrics"]["views"]))
    result["baseline_count"] = len(matches)
    result["baseline_ids"] = [identifier for identifier, _ in matches]
    if len(matches) >= cfg["youtube"]["min_baseline"]:
        typical = median(v for _, v in matches)
        result.update(baseline_median=typical, baseline_method="median_same_format_age_within_35_percent")
        if typical > 0:
            result["outperformance_ratio"] = views/typical
    return result


def support_id(row):
    if row["source"] == "news":
        return row.get("publisher_domain") or "news-unknown-publisher"
    if row["source"] == "youtube":
        return "youtube:"+row["channel_id"]
    return {"trends": "google-search", "reddit": "reddit-discussions", "hackernews": "hn-discussions"}[row["source"]]


def independent_support(rows):
    support, headlines = set(), []
    for row in rows:
        identifier = support_id(row)
        if identifier == "news-unknown-publisher":
            continue
        if row["source"] == "news":
            words = tokens(row["title"])
            # Identical syndicated headlines do not establish independent corroboration.
            if any(len(words & previous)/max(1, len(words | previous)) >= .8 for previous in headlines):
                continue
            headlines.append(words)
        support.add(identifier)
    return support


def bounded_log(value, divisor=4):
    return min(1., max(0., math.log10(1+value)/divisor))


def assess(group, store, cfg, now, search_samples):
    rows = group["signals"]
    title_words = set(plain(" ".join(r["title"] for r in rows)).replace("-", " ").split())
    category = "sensitive" if title_words & SENSITIVE else "ai-tech" if title_words & TECH else "general"
    difficulty = 3 if title_words & COMPLEX else 1 if category == "ai-tech" else 2
    reasons = []
    if category in cfg["excluded_categories"] or cfg["allowed_categories"] and category not in cfg["allowed_categories"]:
        reasons.append("category_filtered")
    if cfg["mode"] == "ai-tech" and category != "ai-tech":
        reasons.append("outside_ai_tech")
    if difficulty > cfg["max_difficulty"]:
        reasons.append("production_too_complex")
    support = independent_support(rows)
    if len(support) < 2:
        reasons.append("insufficient_independent_support")
    if all(r["source"] == "news" for r in rows):
        reasons.append("news_only_without_audience_signal")
    videos = [r for r in rows if r["source"] == "youtube"]
    metrics = [video_metrics(r, store, cfg) for r in videos]
    ratios = [m["outperformance_ratio"] for m in metrics if m["outperformance_ratio"] is not None]
    acceleration = [m["acceleration_ratio"] for m in metrics if m["acceleration_ratio"] is not None]
    rates = [m["interval_views_per_hour"] if m["interval_views_per_hour"] is not None else m["average_views_per_hour"] for m in metrics]
    rates = [r for r in rates if r is not None]
    french = [r for r in rows if r.get("language") == "fr" or r.get("region") == "FR"]
    sampled_ids = {r["video_id"] for r in videos}
    samples = [s for s in search_samples if tokens(s["query"]) & group["tokens"]]
    fr_samples = [s for s in samples if s["language_hint"] == "fr"]
    # Search relevanceLanguage and region are retrieval hints, not language measurements.
    known_fr = len({r["video_id"] for r in videos if r.get("language") == "fr" and r["format"] == "long"})
    unknown = len({r["video_id"] for r in videos if r.get("language") is None})
    competition = "Non mesurée"
    competition_component = None
    if fr_samples and not unknown:
        competition = "Échantillon FR : "+str(known_fr)+" vidéo(s) longue(s)"
        en_count = len({r["video_id"] for r in videos if r.get("language") == "en" and r["format"] == "long"})
        if french and en_count >= 2:
            competition_component = max(0., 1-known_fr/10)
    components = {
        "outperformance": min(1., math.log2(max(1., median(ratios)))/4) if ratios else None,
        "growth": min(1., max(0., median(acceleration)-1)/2) if acceleration else bounded_log(median(rates))*.5 if rates else None,
        "confirmation": min(1., (len(support)-1)/3),
        "competition": competition_component,
        "production": 1. if difficulty == 1 else .6 if difficulty == 2 else 0.,
        "french_relevance": min(1., len({support_id(r) for r in french})/2) if french else None,
    }
    total_weight = sum(cfg["weights"].values())
    contributions = {k: round((v or 0)*cfg["weights"][k]*100/total_weight, 2) for k, v in components.items()}
    score = round(sum(contributions.values()))
    if score < cfg.get("minimum_score", 25):
        reasons.append("below_minimum_score")
    coverage = round(sum(cfg["weights"][k] for k, v in components.items() if v is not None)*100/total_weight)
    confidence = "Élevée" if len(support) >= 3 and len(ratios) >= 2 and acceleration and french else "Moyenne" if len(support) >= 2 and metrics and french else "Faible"
    topic_id = key(group["alias"] or sorted(group["tokens"]))
    previous = store.previous(topic_id)
    if previous and (instant(now)-instant(previous["at"])).total_seconds() < cfg["repeat_after_hours"]*3600 and score < previous["score"]+cfg["repeat_score_increase"]:
        reasons.append("recently_recommended_without_material_change")
    trend = "Accélération mesurée" if acceleration and median(acceleration) > 1.2 else "Ralentissement mesuré" if acceleration and median(acceleration) < .8 else "Vitesse mesurée" if any(m["interval_views_per_hour"] is not None for m in metrics) else "Signal récent, évolution inconnue"
    counts = {str(hours): sum(1 for r in rows if r["published_at"] and 0 <= (instant(now)-instant(r["published_at"])).total_seconds() <= hours*3600) for hours in (24, 48, 168)}
    return {"topic_id": topic_id, "subject": group["title"], "score": score, "confidence": confidence,
            "category": category, "trend": trend, "competition_fr": competition, "competition_unknown_language_count": unknown,
            "search_sample_count": len(samples), "search_sample_matched_ids": sorted(sampled_ids), "complete_market_census": False,
            "production": "Très simple" if difficulty == 1 else "Simple" if difficulty == 2 else "Complexe",
            "production_difficulty_estimate": difficulty, "production_basis": "heuristique lexicale ; droits et faisabilité à vérifier au prepare",
            "duration_seconds_estimate": min(180, cfg["max_video_seconds"]), "scene_count_estimate": 6,
            "components": components, "contributions": contributions, "data_coverage_percent": coverage,
            "missing_criteria": [k for k, v in components.items() if v is None], "support_origins": sorted(support),
            "windows_hours": counts, "video_metrics": metrics, "evidence": rows, "rejection_reasons": reasons,
            "titles": [group["title"], "Comprendre "+group["title"], group["title"]+" : les faits à vérifier"],
            "hook": "Que sait-on de « "+group["title"]+" » ? Partons des sources disponibles.",
            "concept": "Expliquer l'annonce, comparer les éléments confirmés et montrer les limites dans six séquences.",
            "thumbnail": "Un nom de produit lisible et un schéma SVG original ; aucune image de concurrent reprise.",
            "recommendation": "Préparer la recherche primaire avant de produire. Les signaux d'intérêt ne confirment pas les faits du sujet.",
            "rights": "Schémas originaux possibles ; captures et photos à autoriser individuellement. Aucune licence déduite d'un accès public."}


def rank(rows, store, cfg, now, search_samples):
    recent = []
    for row in rows:
        if row.get("role") == "baseline" or not row.get("published_at"):
            continue
        age = (instant(now)-instant(row["published_at"])).total_seconds()
        if 0 <= age <= cfg["window_days"]*86400:
            recent.append(row)
    assessed = [assess(g, store, cfg, now, search_samples) for g in cluster(recent, cfg["topic_aliases"])]
    accepted = sorted((g for g in assessed if not g["rejection_reasons"]), key=lambda g: (-g["score"], g["topic_id"]))
    selected = accepted[:cfg["recommendations"]]
    for index, row in enumerate(selected, 1):
        row["rank"] = index
    return selected, [{"subject": g["subject"], "score": g["score"], "confidence": g["confidence"],
                       "reasons": g["rejection_reasons"] or ["below_selection_cutoff"], "evidence": g["evidence"]} for g in assessed if g not in selected]
