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


PROTECTED_CONFIG_KEYS = frozenset({"mode", "live_enabled", "authorized_accounts", "credentials", "connectors", "storage"})


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


def summarize(observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Conserve les séries distinctes ; aucun total multiréseau ou inter-posts.

    Un même compteur média importé via plusieurs posts partage entity_id et
    n'est donc compté qu'une fois. Les différences de définition, de période ou
    de nature des données restent visibles. Les fenêtres ne sont jamais sommées.
    """
    identities: dict[str, dict] = {}
    series: dict[tuple, list[dict]] = defaultdict(list)
    fields = ("platform", "account_id", "scope", "entity_id", "metric", "unit", "statistic",
              "source", "definition", "definition_version", "data_class", "aggregation_timezone")
    for raw in observations:
        row = validate_observation(raw)
        previous = identities.get(row["observation_id"])
        if previous is not None:
            if previous != row:
                raise ValueError("Deux valeurs contradictoires portent le même observation_id.")
            continue
        identities[row["observation_id"]] = row
        series[tuple(row[key] for key in fields)].append(row)
    result = []
    for key, rows in sorted(series.items()):
        rows.sort(key=lambda row: (_time(row["period_end"]), _time(row["collected_at"]), row["observation_id"]))
        # Counters with different start dates are not the same cumulative series.
        starts = {_time(row["period_start"]) for row in rows}
        overlaps = any(_time(left["period_end"]) > _time(right["period_start"])
                       for index, left in enumerate(rows) for right in rows[index+1:])
        item = dict(zip(fields, key))
        item.update(observations=rows, latest=rows[-1], observation_count=len(rows),
                    aggregation="no_sum", overlapping_periods=overlaps,
                    compatible_cumulative_origin=len(starts) == 1)
        result.append(item)
    return {"series": result, "observation_count": len(identities),
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
    rows = [validate_observation(row) for row in observations]
    related = [row for row in rows if row.get("experiment_id") == current["experiment_id"]
               and row["metric"] == current["primary_metric"]
               and row["data_class"] == "observed"
               and _time(row["period_start"]) >= _time(current["window_start"])
               and _time(row["period_end"]) <= _time(current["window_end"])]
    result = {"experiment_id": current["experiment_id"], "conclusion": "inconclusive", "winner": None,
              "observation_ids": [row["observation_id"] for row in related], "design": current["design"]}
    if instant < _time(current["window_end"]) or current["status"] == "active":
        return {**result, "reason": "experiment_in_progress"}
    if not related:
        return {**result, "reason": "no_observed_variant_results"}
    if current["design"] != "native_randomized":
        return {**result, "reason": "observational_comparison_cannot_establish_a_causal_winner"}
    # A native result may be imported, but never invented from a universal threshold.
    provider = current.get("provider_result", {})
    allowed = {variant["variant_id"] for variant in current["variants"]}
    if {row.get("variant_id") for row in related} != allowed:
        return {**result, "reason": "observed_variant_coverage_incomplete"}
    if (not isinstance(provider, dict) or provider.get("winner") not in allowed
            or not provider.get("evidence") or provider.get("status") != "conclusive"):
        return {**result, "reason": "native_result_missing_or_inconclusive"}
    return {**result, "conclusion": "provider_reported_winner", "winner": provider["winner"],
            "reason": "imported_native_result", "evidence": provider["evidence"],
            "isolated_factor": current["factor"]}


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
