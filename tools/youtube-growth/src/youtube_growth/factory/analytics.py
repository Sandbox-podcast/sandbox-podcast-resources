"""Mesures natives, tests non concluants, coûts et décisions réversibles."""
from __future__ import annotations

from collections import defaultdict
import copy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from typing import Any, Iterable
from zoneinfo import ZoneInfo
from statistics import median


PROTECTED_CONFIG_KEYS = frozenset({"mode", "live_enabled", "authorized_accounts", "credentials", "connectors", "storage", "state_directory", "inbox_directory"})


def compare_content(observations, contexts, *, now=None):
    """Compare observed native series with pairwise compatible exposure and age.

    Contexts map native entity IDs to format, duration, publication date, topic,
    hook and visual style. Missing exposure never becomes zero or a view proxy.
    """
    current = _time(now or datetime.now(timezone.utc))
    context = {}
    for row in contexts:
        _text(row, ("entity_id", "format", "topic", "hook", "visual_style", "provenance"))
        if row["entity_id"] in context:
            raise ValueError("Contexte de contenu dupliqué.")
        if row["format"] not in {"short", "extract", "narrative"}:
            raise ValueError("Format de comparaison inconnu.")
        duration = row.get("duration_seconds")
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
            raise ValueError("Durée de contenu positive requise.")
        if _time(row.get("published_at")) > current:
            raise ValueError("Publication future dans les comparaisons.")
        context[row["entity_id"]] = row
    observed = [r for r in _observations(observations) if r["data_class"] == "observed" and _time(r["collected_at"]) <= current]
    latest = [s["latest"] for s in summarize(observed)["series"]]
    exposure = [r for r in latest if r["metric"] == "impressions"]
    usable, excluded = [], []
    for row in latest:
        meta = context.get(row["entity_id"])
        reason = None
        impressions = next((r for r in exposure if all(r[k] == row[k] for k in
            ("entity_id", "platform", "account_id", "scope", "period_start", "period_end", "statistic"))), None)
        if not meta:
            reason = "content_context_missing"
        elif not impressions or impressions["value"] <= 0:
            reason = "comparable_impressions_missing"
        elif _time(row["period_start"]) < _time(meta["published_at"]):
            reason = "measurement_predates_content"
        if reason:
            excluded.append({"observation_id": row["observation_id"], "reason": reason})
            continue
        age = (_time(row["period_end"])-_time(meta["published_at"])).total_seconds()/86400
        if age <= 0:
            excluded.append({"observation_id": row["observation_id"], "reason": "positive_content_age_required"})
            continue
        usable.append({"observation": row, "context": meta, "age_days": age, "impressions": impressions["value"],
                       "impressions_observation_id": impressions["observation_id"]})
    keys = ("platform", "account_id", "scope", "metric", "unit", "definition", "definition_version", "statistic", "source", "aggregation_timezone")
    groups = []
    def compatible(a, b):
        ar, br = a["observation"], b["observation"]
        return (all(ar[k] == br[k] for k in keys)
                and ar.get("dimensions", {}) == br.get("dimensions", {})
                and ar.get("experiment_id") == br.get("experiment_id") and ar.get("variant_id") == br.get("variant_id")
                and a["context"]["format"] == b["context"]["format"]
                and max(a["context"]["duration_seconds"], b["context"]["duration_seconds"])/min(a["context"]["duration_seconds"], b["context"]["duration_seconds"]) <= 1.3
                and max(a["age_days"], b["age_days"])/min(a["age_days"], b["age_days"]) <= 1.25
                and max(a["impressions"], b["impressions"])/min(a["impressions"], b["impressions"]) <= 2
                and abs((_time(ar["period_end"])-_time(ar["period_start"])).total_seconds()-
                        (_time(br["period_end"])-_time(br["period_start"])).total_seconds()) <= 3600)
    for item in sorted(usable, key=lambda r: r["observation"]["observation_id"]):
        group = next((g for g in groups if all(compatible(item, other) for other in g)), None)
        if group is None:
            groups.append([item])
        else:
            group.append(item)
    cohorts = []
    for group in groups:
        entities = {r["observation"]["entity_id"] for r in group}
        if len(entities) < 2:
            excluded.extend({"observation_id": r["observation"]["observation_id"], "reason": "no_comparable_peer"} for r in group)
            continue
        findings = []
        for dimension in ("topic", "hook", "visual_style"):
            labels = {r["context"][dimension] for r in group}
            findings.extend({"dimension": dimension, "label": label,
                             "median": median(r["observation"]["value"] for r in group if r["context"][dimension] == label),
                             "sample_size": sum(r["context"][dimension] == label for r in group)} for label in sorted(labels))
        cohorts.append({"metric": group[0]["observation"]["metric"], "format": group[0]["context"]["format"],
                        "members": group, "findings": findings, "status": "descriptive_only", "causal_winner": None})
    return {"cohorts": cohorts, "excluded": excluded, "synthetic_excluded": sum(r["data_class"] != "observed" for r in observations),
            "automatic_strategy_change": False, "limits": {"duration_ratio": 1.3, "age_ratio": 1.25, "exposure_ratio": 2,
            "period_length_tolerance_seconds": 3600}, "interpretation": "Hypothèses à tester ; aucune causalité déduite des corrélations."}


def _time(value: Any) -> datetime:
    if not isinstance(value, (str, datetime)):
        raise ValueError("Instant ISO 8601 avec fuseau requis.")
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Un instant sans fuseau est ambigu.")
    return result.astimezone(timezone.utc)


def _text(row: dict, names: Iterable[str]) -> None:
    for name in names:
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise ValueError(f"{name} requis.")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_observation(row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError("Observation objet requise.")
    _text(row, ("observation_id", "platform", "account_id", "scope", "entity_id", "metric", "unit",
                "source", "aggregation_timezone", "definition", "definition_version", "data_class"))
    if row["scope"] not in {"account", "post", "media", "destination", "experiment"}:
        raise ValueError("Périmètre de métrique inconnu.")
    if row.get("statistic") not in {"cumulative", "interval", "gauge"}:
        raise ValueError("Nature cumulative, interval ou gauge requise.")
    if row["data_class"] not in {"observed", "synthetic_fixture"}:
        raise ValueError("Origine observée ou fixture explicite requise.")
    for field in ("experiment_id", "variant_id", "publication_id"):
        if row.get(field) is not None:
            _text(row, (field,))
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Une valeur absente n'est pas une observation à zéro.")
    if "denominator" not in row:
        raise ValueError("Dénominateur explicite requis ; null si non applicable ou indisponible.")
    denominator = row["denominator"]
    if denominator is not None and (isinstance(denominator, bool) or not isinstance(denominator, (int, float))
                                    or not math.isfinite(denominator) or denominator <= 0):
        raise ValueError("Dénominateur positif requis lorsqu'il est connu.")
    start, end, collected = (_time(row.get(name)) for name in ("period_start", "period_end", "collected_at"))
    if start > end or end > collected:
        raise ValueError("Période et date de collecte incohérentes.")
    ZoneInfo(row["aggregation_timezone"])
    return copy.deepcopy(row)


def _observations(observations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    identities = {}
    for raw in observations:
        row = validate_observation(raw)
        previous = identities.get(row["observation_id"])
        if previous is not None and previous != row:
            raise ValueError("Deux valeurs contradictoires portent le même observation_id.")
        identities[row["observation_id"]] = row
    return list(identities.values())


def summarize(observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Conserve les séries distinctes ; aucun total multiréseau ou inter-posts.

    Un même compteur média importé via plusieurs posts partage entity_id et
    n'est donc compté qu'une fois. Les différences de définition, de période ou
    de nature des données restent visibles. Les fenêtres ne sont jamais sommées.
    """
    series: dict[tuple, list[dict]] = defaultdict(list)
    fields = ("platform", "account_id", "scope", "entity_id", "metric", "unit", "statistic",
              "source", "definition", "definition_version", "data_class", "aggregation_timezone",
              "experiment_id", "variant_id")
    validated = _observations(observations)
    for row in validated:
        series[tuple(row.get(key) or "" for key in fields)+(_hash(row.get("dimensions", {})),)].append(row)
    result = []
    for key, rows in sorted(series.items()):
        rows.sort(key=lambda row: (_time(row["period_end"]), _time(row["collected_at"]), row["observation_id"]))
        # Counters with different start dates are not the same cumulative series.
        starts = {_time(row["period_start"]) for row in rows}
        # Sorting by start and retaining the furthest end detects nested periods
        # too, without comparing every pair in long, non-overlapping histories.
        periods = sorted((_time(row["period_start"]), _time(row["period_end"])) for row in rows)
        overlaps, furthest_end = False, None
        for start, end in periods:
            if furthest_end is not None and start < furthest_end:
                overlaps = True
                break
            furthest_end = end if furthest_end is None else max(furthest_end, end)
        item = dict(zip(fields, key))
        item["dimensions"] = rows[-1].get("dimensions", {})
        item.update(observations=rows, latest=rows[-1], observation_count=len(rows),
                    aggregation="no_sum", overlapping_periods=overlaps,
                    compatible_cumulative_origin=len(starts) == 1)
        result.append(item)
    return {"series": result, "observation_count": len(validated),
            "unavailable_metrics": "absent", "cross_platform_unique_audience": None,
            "attribution": {"observed_clicks": "available_only_if_observed",
                            "youtube_arrivals": "available_only_if_observed",
                            "long_form_views": "available_only_if_observed",
                            "attributed_subscriptions": "available_only_if_observed",
                            "individual_journey": "unknown"}}


def validate_experiment(experiment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(experiment, dict):
        raise ValueError("Expérience objet requise.")
    _text(experiment, ("experiment_id", "hypothesis", "publication_id", "factor", "primary_metric",
                       "observable_population", "stop_condition", "decision_rule", "design", "status"))
    variants = experiment.get("variants")
    if not isinstance(variants, list) or not 2 <= len(variants) <= 3:
        raise ValueError("Deux ou trois variantes sont requises pour une comparaison.")
    ids = []
    for variant in variants:
        if not isinstance(variant, dict):
            raise ValueError("Variante objet requise.")
        _text(variant, ("variant_id", "hypothesis"))
        ids.append(variant["variant_id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Identifiants de variantes dupliqués.")
    if experiment["design"] not in {"native_randomized", "sequential_observational", "observational"}:
        raise ValueError("Méthode d'expérience inconnue.")
    if experiment["design"] == "native_randomized":
        _text(experiment, ("provider_experiment_id", "randomization_evidence"))
    if experiment["status"] not in {"draft", "active", "complete", "stopped"}:
        raise ValueError("État d'expérience inconnu.")
    if _time(experiment.get("window_start")) >= _time(experiment.get("window_end")):
        raise ValueError("Fenêtre d'expérience vide.")
    changed = experiment.get("changed_fields", [experiment["factor"]])
    if not isinstance(changed, list) or not changed or any(not isinstance(field, str) for field in changed):
        raise ValueError("Facteurs modifiés requis.")
    if len(changed) > 1 and experiment["factor"] != "combination":
        raise ValueError("Plusieurs champs modifiés doivent être analysés comme une combinaison.")
    return copy.deepcopy(experiment)


def ensure_packaging_unlocked(publication_id: str, experiments: Iterable[dict[str, Any]]) -> None:
    for experiment in experiments:
        current = validate_experiment(experiment)
        if current["publication_id"] == publication_id and current["status"] == "active":
            raise ValueError("Le packaging est réservé par une expérience active.")


def conclude_experiment(experiment: dict[str, Any], observations: Iterable[dict[str, Any]], *,
                        now: str | datetime | None = None) -> dict[str, Any]:
    current = validate_experiment(experiment)
    instant = _time(now or datetime.now(timezone.utc))
    rows = _observations(observations)
    related = [row for row in rows if row.get("experiment_id") == current["experiment_id"]
               and row["metric"] == current["primary_metric"]
               and row.get("publication_id") == current["publication_id"]
               and row["data_class"] == "observed"
               and _time(row["collected_at"]) <= instant
               and all(not current.get(field) or row[field] == current[field] for field in ("platform", "account_id"))
               and _time(row["period_start"]) >= _time(current["window_start"])
               and _time(row["period_end"]) <= _time(current["window_end"])]
    result = {"experiment_id": current["experiment_id"], "conclusion": "inconclusive", "winner": None,
              "observation_ids": [row["observation_id"] for row in related], "design": current["design"]}
    if instant < _time(current["window_end"]) or current["status"] == "active":
        return {**result, "reason": "experiment_in_progress"}
    if current["status"] != "complete":
        return {**result, "reason": "experiment_not_completed"}
    if not related:
        return {**result, "reason": "no_observed_variant_results"}
    if current["design"] != "native_randomized":
        return {**result, "reason": "observational_comparison_cannot_establish_a_causal_winner"}
    comparable_fields = ("platform", "account_id", "scope", "unit", "statistic", "source",
                         "definition", "definition_version", "aggregation_timezone")
    if len({tuple(row[field] for field in comparable_fields) for row in related}) != 1:
        return {**result, "reason": "incompatible_variant_measurements"}
    # A native result may be imported, but never invented from a universal threshold.
    provider = current.get("provider_result", {})
    allowed = {variant["variant_id"] for variant in current["variants"]}
    if {row.get("variant_id") for row in related} != allowed:
        return {**result, "reason": "observed_variant_coverage_incomplete"}
    latest = {variant: max((row for row in related if row.get("variant_id") == variant),
                           key=lambda row: (_time(row["period_end"]), _time(row["collected_at"])))
              for variant in allowed}
    if len({(_time(row["period_start"]), _time(row["period_end"])) for row in latest.values()}) != 1:
        return {**result, "reason": "incompatible_variant_periods"}
    if (not isinstance(provider, dict) or provider.get("winner") not in allowed
            or not provider.get("evidence") or provider.get("status") != "conclusive"):
        return {**result, "reason": "native_result_missing_or_inconclusive"}
    return {**result, "conclusion": "provider_reported_winner", "winner": provider["winner"],
            "reason": "imported_native_result", "evidence": provider["evidence"],
            "isolated_factor": current["factor"]}


def learning_brief(observations: Iterable[dict[str, Any]], experiments: Iterable[dict[str, Any]] = (),
                   decisions: Iterable[dict[str, Any]] = (), *,
                   now: str | datetime | None = None,
                   decision_observations: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the next review from available evidence, without changing strategy.

    The brief retains native units and scopes. It never ranks unrelated videos,
    invents a target metric or turns a native result into a universal rule.
    """
    instant = _time(now or datetime.now(timezone.utc))
    rows = _observations(observations)
    available = [row for row in rows if row["data_class"] == "observed" and _time(row["collected_at"]) <= instant]
    # Decisions can span episodes even when performance facts are filtered.
    decision_rows = rows if decision_observations is None else _observations(decision_observations)
    available_by_id = {row["observation_id"]: row for row in decision_rows
                       if row["data_class"] == "observed" and _time(row["collected_at"]) <= instant}
    all_by_id = {row["observation_id"]: row for row in decision_rows}
    summary = summarize(available)
    facts = []
    for series in summary["series"]:
        latest = series["latest"]
        facts.append({key: copy.deepcopy(latest.get(key)) for key in (
            "observation_id", "platform", "account_id", "scope", "entity_id", "publication_id",
            "metric", "value", "unit", "denominator", "statistic", "period_start", "period_end",
            "collected_at", "aggregation_timezone", "source", "definition", "definition_version",
            "experiment_id", "variant_id")})
    actions = []
    if not available:
        actions.append({"action": "collect_observed_results", "priority": "high", "observation_ids": [],
                        "reason": "Importer des résultats réels avec leurs périodes et leur provenance avant de décider d'un changement."})
    experiment_results = []
    for experiment in experiments:
        result = conclude_experiment(experiment, rows, now=instant)
        experiment_results.append({**result, "hypothesis": experiment["hypothesis"],
                                   "publication_id": experiment["publication_id"],
                                   "primary_metric": experiment["primary_metric"]})
        if result["reason"] not in {"experiment_in_progress", "experiment_not_completed"}:
            actions.append({"action": "review_experiment" if result["winner"] else "resolve_inconclusive_experiment",
                            "priority": "normal", "experiment_id": result["experiment_id"],
                            "observation_ids": result["observation_ids"], "reason": result["reason"]})
    decision_reviews = []
    for decision in decisions:
        _text(decision, ("decision_id", "reason", "reevaluate_at"))
        observation_ids = decision.get("observation_ids")
        if not isinstance(observation_ids, list) or not observation_ids or any(not isinstance(key, str) for key in observation_ids):
            raise ValueError("Les observations sources d'une décision sont requises pour son bilan.")
        missing = [key for key in observation_ids if key not in all_by_id]
        unavailable = [key for key in observation_ids if key in all_by_id and key not in available_by_id]
        due = _time(decision["reevaluate_at"]) <= instant
        review = {"decision_id": decision["decision_id"], "reason": decision["reason"],
                  "reevaluate_at": decision["reevaluate_at"], "reevaluation_due": due,
                  "observation_ids": list(dict.fromkeys(observation_ids)), "missing_observation_ids": missing,
                  "unavailable_observation_ids": unavailable,
                  "evidence_status": "missing" if missing else "unavailable" if unavailable else "observed",
                  "application_status": "not_inferred_from_proposal"}
        decision_reviews.append(review)
        if due or missing or unavailable:
            actions.append({"action": "reevaluate_decision" if due else "complete_decision_evidence",
                            "priority": "high", "decision_id": decision["decision_id"],
                            "observation_ids": review["observation_ids"],
                            "reason": "Échéance de réévaluation atteinte." if due else "Les preuves réelles citées restent incomplètes."})
    return {"generated_at": instant.isoformat(), "status": "observed_evidence_available" if available else "no_observed_evidence",
            "observed_count": len(available), "synthetic_count": sum(row["data_class"] == "synthetic_fixture" for row in rows),
            "future_observed_count": sum(row["data_class"] == "observed" and _time(row["collected_at"]) > instant for row in rows),
            "facts": facts, "experiments": experiment_results, "decisions_to_review": decision_reviews,
            "recommended_actions": actions, "automatic_changes": False,
            "limits": ["Une mesure absente reste inconnue ; elle ne vaut pas zéro.",
                       "Un résultat natif porte sur sa vidéo, sa population et sa période.",
                       "Les propositions ne prouvent pas qu'une configuration a été appliquée."]}


def _amount(value: Any) -> Decimal:
    try:
        if isinstance(value, bool):
            raise ValueError("Coût numérique requis.")
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise ValueError("Coût fini et positif ou nul requis.")
        return result
    except InvalidOperation as error:
        raise ValueError("Coût numérique requis.") from error


def budget_status(records: Iterable[dict[str, Any]], limits: dict[str, Any]) -> dict[str, Any]:
    """Compare dépenses et engagements estimés dans une devise unique.

    limits = {currency, episode_max, stage_max: {stage: amount}, usable_content_count}.
    Une dépense réalisée peut remplacer une estimation via linked_estimate_id.
    """
    _text(limits, ("currency",))
    unique: dict[str, dict] = {}
    for row in records:
        _text(row, ("cost_id", "episode_id", "stage", "currency", "kind"))
        if row["currency"] != limits["currency"]:
            raise ValueError("Conversion de devise requise avant de comparer les coûts.")
        if row["kind"] not in {"observed", "estimated"}:
            raise ValueError("Coût observé ou estimé requis.")
        _amount(row.get("amount"))
        _time(row.get("recorded_at"))
        if row["cost_id"] in unique and unique[row["cost_id"]] != row:
            raise ValueError("Coût dupliqué avec une valeur contradictoire.")
        unique[row["cost_id"]] = copy.deepcopy(row)
    rows = list(unique.values())
    replaced = {row["linked_estimate_id"] for row in rows if row["kind"] == "observed" and row.get("linked_estimate_id")}
    for row in rows:
        if row["kind"] == "observed" and row.get("linked_estimate_id"):
            estimate = unique.get(row["linked_estimate_id"])
            if (not estimate or estimate["kind"] != "estimated" or
                    (estimate["episode_id"], estimate["stage"]) != (row["episode_id"], row["stage"])):
                raise ValueError("Estimation remplacée absente ou liée à un autre épisode/étape.")
    active = [row for row in rows if row["kind"] == "observed" or row["cost_id"] not in replaced]
    observed = sum((_amount(row["amount"]) for row in rows if row["kind"] == "observed"), Decimal(0))
    estimated = sum((_amount(row["amount"]) for row in active if row["kind"] == "estimated"), Decimal(0))
    episode_totals: dict[str, Decimal] = defaultdict(Decimal)
    stage_totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for row in active:
        episode_totals[row["episode_id"]] += _amount(row["amount"])
        stage_totals[row["episode_id"], row["stage"]] += _amount(row["amount"])
    blockers = []
    if "episode_max" in limits:
        maximum = _amount(limits["episode_max"])
        blockers.extend(f"episode_budget_reached:{episode}" for episode, total in episode_totals.items() if total >= maximum)
    for (episode, stage), total in stage_totals.items():
        if stage in limits.get("stage_max", {}) and total >= _amount(limits["stage_max"][stage]):
            blockers.append(f"stage_budget_reached:{episode}:{stage}")
    usable = limits.get("usable_content_count")
    if usable is not None and (isinstance(usable, bool) or not isinstance(usable, int) or usable < 0):
        raise ValueError("Nombre de contenus utilisables entier positif ou nul requis.")
    return {"currency": limits["currency"], "observed": float(observed) if any(row["kind"] == "observed" for row in rows) else None,
            "estimated_open": float(estimated) if any(row["kind"] == "estimated" for row in active) else None,
            "projected": float(observed + estimated) if rows else None,
            "cost_per_usable_content": float(observed / usable) if usable and any(row["kind"] == "observed" for row in rows) else None,
            "by_episode": {key: float(value) for key, value in episode_totals.items()},
            "blockers": blockers, "allowed": not blockers,
            "on_limit": "block_new_costs_preserve_existing_results"}


def _merge(target: dict, changes: dict) -> dict:
    result = copy.deepcopy(target)
    for key, value in changes.items():
        if key not in target:
            raise ValueError("Une décision ne peut modifier une clé de configuration inconnue.")
        if isinstance(value, dict) and isinstance(target[key], dict):
            result[key] = _merge(target[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def make_decision(config: dict[str, Any], changes: dict[str, Any], *, reason: str,
                  observation_ids: list[str], recorded_at: str, reevaluate_at: str) -> dict[str, Any]:
    if not isinstance(config, dict) or not isinstance(changes, dict) or not changes:
        raise ValueError("Configuration et changements explicites requis.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Motif de décision requis.")
    if (not isinstance(observation_ids, list) or not observation_ids
            or any(not isinstance(value, str) or not value.strip() for value in observation_ids)):
        raise ValueError("Observations sources requises.")
    if _time(recorded_at) >= _time(reevaluate_at):
        raise ValueError("Date de réévaluation ultérieure requise.")
    # Neither learning nor a fixture may activate writes or expand account access.
    if set(changes) & PROTECTED_CONFIG_KEYS:
        raise ValueError("Une décision d'apprentissage ne peut élargir les accès ou activer la diffusion.")
    updated = _merge(config, changes)
    result = {"version": 1, "reason": reason.strip(), "observation_ids": list(dict.fromkeys(observation_ids)),
              "recorded_at": _time(recorded_at).isoformat(), "reevaluate_at": _time(reevaluate_at).isoformat(),
              "previous": copy.deepcopy(config), "new": updated,
              "previous_sha256": _hash(config), "new_sha256": _hash(updated), "changes": copy.deepcopy(changes)}
    return {"decision_id": "decision:" + _hash(result)[:24], **result}


def apply_decision(config: dict[str, Any], decision: dict[str, Any], *, reverse: bool = False) -> dict[str, Any]:
    if decision.get("version") != 1:
        raise ValueError("Version de décision inconnue.")
    identity = {key: value for key, value in decision.items() if key != "decision_id"}
    if decision.get("decision_id") != "decision:" + _hash(identity)[:24]:
        raise ValueError("La décision a changé depuis sa préparation.")
    if any(decision["previous"].get(key) != decision["new"].get(key) for key in PROTECTED_CONFIG_KEYS):
        raise ValueError("La décision importée modifie les accès ou le stockage.")
    expected, target = ("new", "previous") if reverse else ("previous", "new")
    if _hash(config) != decision.get(expected + "_sha256"):
        raise ValueError("La configuration a changé ; réconcilier avant application ou restauration.")
    if _hash(decision[target]) != decision.get(target + "_sha256"):
        raise ValueError("L'empreinte de décision est invalide.")
    return copy.deepcopy(decision[target])
