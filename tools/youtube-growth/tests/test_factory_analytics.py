from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory.analytics import (apply_decision, budget_status, conclude_experiment,
                                              ensure_packaging_unlocked, make_decision, summarize,
                                              validate_experiment, validate_observation)


def observation(**values):
    return {"observation_id": "obs-1", "platform": "youtube", "account_id": "channel", "scope": "post",
            "entity_id": "remote-1", "publication_id": "pub-1", "metric": "views", "value": 10,
            "unit": "count", "statistic": "cumulative", "denominator": None, "source": "data-api",
            "data_class": "observed", "period_start": "2026-10-20T10:00:00+02:00",
            "period_end": "2026-10-21T10:00:00+02:00", "collected_at": "2026-10-22T10:00:00+02:00",
            "aggregation_timezone": "America/Los_Angeles", "definition": "Native video view count",
            "definition_version": "v3", **values}


def experiment(**values):
    return {"experiment_id": "exp-1", "hypothesis": "Une question précise attire le public concerné.",
            "publication_id": "pub-1", "factor": "title", "primary_metric": "thumbnail_ctr",
            "observable_population": "Impressions de miniature éligibles de la vidéo.",
            "stop_condition": "Fin du test natif ou arrêt du fournisseur.",
            "decision_rule": "Conserver un résultat non concluant si le fournisseur ne tranche pas.",
            "design": "sequential_observational", "status": "complete",
            "window_start": "2026-10-20T10:00:00+02:00", "window_end": "2026-10-27T10:00:00+01:00",
            "variants": [{"variant_id": "a", "hypothesis": "Question"},
                         {"variant_id": "b", "hypothesis": "Conséquence"}], **values}


class FactoryAnalyticsTests(unittest.TestCase):
    def test_missing_is_absent_and_not_zero(self):
        self.assertEqual(summarize([])["series"], [])
        self.assertIsNone(summarize([])["cross_platform_unique_audience"])
        for value in (None, float("nan"), True):
            with self.assertRaises(ValueError):
                validate_observation(observation(value=value))
        self.assertEqual(validate_observation(observation(value=0))["value"], 0)

    def test_ambiguous_dates_and_bad_denominators_are_refused(self):
        for values in ({"period_start": "2026-10-20T10:00:00"}, {"denominator": 0},
                       {"period_end": "2026-10-23T10:00:00+02:00"}):
            with self.assertRaises(ValueError):
                validate_observation(observation(**values))

    def test_cumulative_snapshots_and_overlapping_windows_are_never_summed(self):
        rows = [observation(), observation(observation_id="obs-2", value=18,
                                           period_end="2026-10-22T10:00:00+02:00")]
        summary = summarize(rows)
        self.assertEqual(len(summary["series"]), 1)
        self.assertEqual(summary["series"][0]["latest"]["value"], 18)
        self.assertEqual(summary["series"][0]["aggregation"], "no_sum")
        self.assertTrue(summary["series"][0]["overlapping_periods"])
        self.assertNotIn("total_views", summary)

    def test_different_platforms_media_definitions_and_fixtures_stay_separate(self):
        rows = [observation(), observation(observation_id="obs-2", platform="tiktok"),
                observation(observation_id="obs-3", data_class="synthetic_fixture"),
                observation(observation_id="obs-4", definition_version="v4")]
        self.assertEqual(len(summarize(rows)["series"]), 4)

    def test_repeated_import_is_idempotent_but_conflicting_observation_fails(self):
        self.assertEqual(summarize([observation(), observation()])["observation_count"], 1)
        with self.assertRaises(ValueError):
            summarize([observation(), observation(value=11)])

    def test_shared_media_counter_is_one_series_across_posts(self):
        first = observation(scope="media", entity_id="video-1")
        second = observation(observation_id="obs-2", scope="media", entity_id="video-1", publication_id="pub-2")
        self.assertEqual(len(summarize([first, second])["series"]), 1)

    def test_empty_and_observational_experiments_are_inconclusive(self):
        current = experiment()
        self.assertEqual(conclude_experiment(current, [], now="2026-10-28T12:00:00Z")["conclusion"], "inconclusive")
        row = observation(experiment_id="exp-1", metric="thumbnail_ctr", variant_id="a")
        second = {**row, "variant_id": "b", "observation_id": "obs-2"}
        self.assertEqual(conclude_experiment(current, [row], now="2026-10-28T12:00:00Z")["conclusion"], "inconclusive")
        result = conclude_experiment(current, [row, second], now="2026-10-28T12:00:00Z")
        self.assertEqual(result["conclusion"], "inconclusive")
        self.assertIn("observational", result["reason"])

    def test_native_randomization_requires_evidence_and_combined_fields_are_not_isolated(self):
        with self.assertRaises(ValueError):
            validate_experiment(experiment(design="native_randomized"))
        with self.assertRaises(ValueError):
            validate_experiment(experiment(changed_fields=["title", "thumbnail"]))
        validate_experiment(experiment(factor="combination", changed_fields=["title", "thumbnail"]))
        active = experiment(status="active")
        with self.assertRaises(ValueError):
            ensure_packaging_unlocked("pub-1", [active])
        ensure_packaging_unlocked("another-publication", [active])

    def test_native_result_is_imported_with_provenance_and_no_invented_threshold(self):
        current = experiment(design="native_randomized", provider_experiment_id="native-test",
                             randomization_evidence="studio-export.json",
                             provider_result={"winner": "b", "status": "conclusive", "evidence": "studio-result.json"})
        row = observation(experiment_id="exp-1", metric="thumbnail_ctr", variant_id="a")
        second = {**row, "variant_id": "b", "observation_id": "obs-2"}
        self.assertEqual(conclude_experiment(current, [row], now="2026-10-28T12:00:00Z")["conclusion"], "inconclusive")
        result = conclude_experiment(current, [row, second], now="2026-10-28T12:00:00Z")
        self.assertEqual(result["winner"], "b")
        self.assertEqual(result["conclusion"], "provider_reported_winner")
        fixture = {**row, "data_class": "synthetic_fixture"}
        self.assertIsNone(conclude_experiment(current, [fixture], now="2026-10-28T12:00:00Z")["winner"])

    def test_costs_estimates_actuals_and_replaced_estimates_are_separate(self):
        estimate = {"cost_id": "estimate-1", "episode_id": "episode-1", "stage": "transcription",
                    "currency": "EUR", "kind": "estimated", "amount": "2.50", "recorded_at": "2026-10-28T10:00:00Z"}
        actual = {**estimate, "cost_id": "actual-1", "kind": "observed", "amount": "2.00",
                  "linked_estimate_id": "estimate-1"}
        result = budget_status([estimate, actual, copy.deepcopy(actual)], {"currency": "EUR", "episode_max": 3,
                                                                         "usable_content_count": 2})
        self.assertEqual(result["observed"], 2)
        self.assertIsNone(result["estimated_open"])
        self.assertEqual(result["projected"], 2)
        self.assertEqual(result["cost_per_usable_content"], 1)
        self.assertTrue(result["allowed"])
        self.assertFalse(budget_status([estimate], {"currency": "EUR", "episode_max": "2.50"})["allowed"])
        self.assertIsNone(budget_status([], {"currency": "EUR"})["observed"])

    def test_costs_from_different_currencies_are_not_added(self):
        with self.assertRaises(ValueError):
            budget_status([{"cost_id": "x", "episode_id": "e", "stage": "render", "currency": "USD", "kind": "observed",
                            "amount": 1, "recorded_at": "2026-10-28T10:00:00Z"}], {"currency": "EUR"})

    def test_learning_decisions_are_reversible_and_reject_stale_config(self):
        config = {"mode": "simulation", "live_enabled": False, "cadence": {"x": 1}, "authorized_accounts": {}}
        decision = make_decision(config, {"cadence": {"x": 2}}, reason="Deux essais observés.",
                                 observation_ids=["obs-1", "obs-2"], recorded_at="2026-10-28T10:00:00Z",
                                 reevaluate_at="2026-11-04T10:00:00Z")
        changed = apply_decision(config, decision)
        self.assertEqual(changed["cadence"]["x"], 2)
        self.assertEqual(apply_decision(changed, decision, reverse=True), config)
        with self.assertRaises(ValueError):
            apply_decision(changed, decision)
        altered = copy.deepcopy(decision)
        altered["reason"] = "Motif changé après préparation."
        with self.assertRaises(ValueError):
            apply_decision(config, altered)
        with self.assertRaises(ValueError):
            make_decision(config, {"live_enabled": True}, reason="Accès", observation_ids=["obs-1"],
                          recorded_at="2026-10-28T10:00:00Z", reevaluate_at="2026-11-04T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
