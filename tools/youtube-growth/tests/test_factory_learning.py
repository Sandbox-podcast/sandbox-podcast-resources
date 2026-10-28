"""Evidence separation, review actions and bounded work on analytics histories."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube_growth.factory import analytics
from test_factory_analytics import experiment, observation


NOW = "2026-10-28T12:00:00Z"


def native_experiment(**changes):
    return experiment(design="native_randomized", provider_experiment_id="native-test",
                      randomization_evidence="studio-export.json",
                      provider_result={"winner": "b", "status": "conclusive", "evidence": "studio-result.json"},
                      **changes)


def variants():
    return [observation(observation_id="obs-"+variant, experiment_id="exp-1", metric="thumbnail_ctr",
                        variant_id=variant, value=value) for variant, value in (("a", 3), ("b", 4))]


class FactoryLearningTests(unittest.TestCase):
    def test_experimental_variants_never_replace_each_other_in_latest_series(self):
        result = analytics.summarize(variants())
        self.assertEqual(len(result["series"]), 2)
        self.assertEqual({row["variant_id"]: row["latest"]["value"] for row in result["series"]}, {"a": 3, "b": 4})
        unrelated = observation(experiment_id="different-test", variant_id="a")
        self.assertEqual(len(analytics.summarize(variants()+[unrelated])["series"]), 3)

    def test_disjoint_history_has_bounded_date_parsing_and_no_overlap(self):
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        rows = [observation(observation_id=str(index), statistic="interval",
                            period_start=(base+timedelta(days=index)).isoformat(),
                            period_end=(base+timedelta(days=index+1)).isoformat()) for index in range(600)]
        with patch.object(analytics, "_time", wraps=analytics._time) as parse:
            result = analytics.summarize(rows)
        self.assertFalse(result["series"][0]["overlapping_periods"])
        self.assertEqual(result["series"][0]["observation_count"], 600)
        self.assertLess(parse.call_count, len(rows)*20)

    def test_nested_and_touching_intervals_are_distinguished(self):
        wide = observation(period_start="2026-10-01T00:00:00Z", period_end="2026-10-22T00:00:00Z")
        inside = observation(observation_id="inside", period_start="2026-10-20T00:00:00Z",
                             period_end="2026-10-21T00:00:00Z")
        self.assertTrue(analytics.summarize([wide, inside])["series"][0]["overlapping_periods"])
        touching = observation(observation_id="touching", period_start="2026-10-21T00:00:00Z",
                               period_end="2026-10-22T00:00:00Z")
        self.assertFalse(analytics.summarize([inside, touching])["series"][0]["overlapping_periods"])

    def test_wrong_publication_and_future_data_do_not_supply_missing_variant(self):
        for changes in ({"publication_id": "different-publication"}, {"publication_id": None},
                        {"collected_at": "2026-11-01T12:00:00Z"}, {"data_class": "synthetic_fixture"}):
            with self.subTest(changes=changes):
                rows = variants()
                rows[1].update(changes)
                result = analytics.conclude_experiment(native_experiment(), rows, now=NOW)
                self.assertIsNone(result["winner"])
                self.assertEqual(result["observation_ids"], ["obs-a"])

    def test_incompatible_metrics_cannot_support_a_native_result(self):
        for field, value in (("unit", "percent"), ("definition_version", "changed"),
                             ("platform", "tiktok"), ("account_id", "other-channel"),
                             ("statistic", "gauge"), ("aggregation_timezone", "UTC")):
            with self.subTest(field=field):
                rows = variants()
                rows[1][field] = value
                result = analytics.conclude_experiment(native_experiment(), rows, now=NOW)
                self.assertIsNone(result["winner"])
                self.assertEqual(result["reason"], "incompatible_variant_measurements")

    def test_experiment_account_and_platform_filters_are_respected(self):
        current = native_experiment(account_id="expected", platform="youtube")
        rows = variants()
        self.assertIsNone(analytics.conclude_experiment(current, rows, now=NOW)["winner"])
        for row in rows:
            row["account_id"] = "expected"
        self.assertEqual(analytics.conclude_experiment(current, rows, now=NOW)["winner"], "b")

    def test_variant_latest_periods_must_match(self):
        rows = variants()
        rows[1]["period_start"] = "2026-10-21T00:00:00Z"
        result = analytics.conclude_experiment(native_experiment(), rows, now=NOW)
        self.assertIsNone(result["winner"])
        self.assertEqual(result["reason"], "incompatible_variant_periods")

    def test_duplicates_are_deduplicated_and_conflicts_fail_in_experiments(self):
        rows = variants()
        result = analytics.conclude_experiment(native_experiment(), rows+rows, now=NOW)
        self.assertEqual(result["observation_ids"], ["obs-a", "obs-b"])
        with self.assertRaises(ValueError):
            analytics.conclude_experiment(native_experiment(), rows+[{**rows[0], "value": 100}], now=NOW)

    def test_draft_stopped_and_active_experiments_cannot_claim_winner(self):
        for status in ("draft", "stopped", "active"):
            with self.subTest(status=status):
                result = analytics.conclude_experiment(native_experiment(status=status), variants(), now=NOW)
                self.assertIsNone(result["winner"])

    def test_fixture_only_brief_has_no_performance_facts_and_requests_observed_data(self):
        rows = [observation(data_class="synthetic_fixture", value=100000)]
        result = analytics.learning_brief(rows, now=NOW)
        self.assertEqual(result["status"], "no_observed_evidence")
        self.assertEqual(result["synthetic_count"], 1)
        self.assertEqual(result["observed_count"], 0)
        self.assertEqual(result["facts"], [])
        self.assertFalse(result["automatic_changes"])
        self.assertEqual(result["recommended_actions"][0]["action"], "collect_observed_results")

    def test_brief_preserves_native_zero_and_provenance_but_excludes_future(self):
        rows = [observation(value=0), observation(observation_id="future", value=100,
                                                collected_at="2026-11-01T00:00:00Z")]
        result = analytics.learning_brief(iter(rows), now=NOW)
        self.assertEqual(result["observed_count"], 1)
        self.assertEqual(result["future_observed_count"], 1)
        fact = result["facts"][0]
        self.assertEqual(fact["value"], 0)
        self.assertEqual(fact["observation_id"], "obs-1")
        for key in ("definition", "definition_version", "source", "period_start", "period_end", "unit", "scope"):
            self.assertEqual(fact[key], rows[0][key])
        self.assertIsNone(fact["denominator"])

    def test_brief_surfaces_reevaluation_and_missing_or_synthetic_evidence(self):
        config = {"cadence": 1}
        decision = analytics.make_decision(config, {"cadence": 2}, reason="Observation à réexaminer.",
                                           observation_ids=["missing", "fixture", "obs-1"],
                                           recorded_at="2026-10-20T00:00:00Z", reevaluate_at=NOW)
        rows = [observation(), observation(observation_id="fixture", data_class="synthetic_fixture")]
        original = copy.deepcopy(decision)
        result = analytics.learning_brief(rows, decisions=[decision], now=NOW)
        review = result["decisions_to_review"][0]
        self.assertTrue(review["reevaluation_due"])
        self.assertEqual(review["missing_observation_ids"], ["missing"])
        self.assertEqual(review["unavailable_observation_ids"], ["fixture"])
        self.assertEqual(review["application_status"], "not_inferred_from_proposal")
        self.assertEqual(result["recommended_actions"][0]["action"], "reevaluate_decision")
        self.assertEqual(decision, original)

    def test_brief_reuses_native_result_without_generalizing_it(self):
        result = analytics.learning_brief(variants(), [native_experiment()], now=NOW)
        self.assertEqual(result["experiments"][0]["winner"], "b")
        self.assertEqual(result["experiments"][0]["evidence"], "studio-result.json")
        self.assertEqual(result["recommended_actions"][0]["action"], "review_experiment")
        self.assertFalse(result["automatic_changes"])

    def test_global_decision_evidence_does_not_pollute_episode_facts(self):
        scoped = observation(observation_id="current-episode", episode_id="episode-2")
        external = observation(observation_id="other-episode", episode_id="episode-1")
        decision = analytics.make_decision({"cadence": 1}, {"cadence": 2}, reason="Résultat du cycle précédent.",
                                           observation_ids=["other-episode"], recorded_at="2026-10-20T00:00:00Z",
                                           reevaluate_at="2026-11-04T00:00:00Z")
        result = analytics.learning_brief([scoped], decisions=[decision], now=NOW,
                                          decision_observations=iter([external, scoped]))
        self.assertEqual([fact["observation_id"] for fact in result["facts"]], ["current-episode"])
        self.assertEqual(result["observed_count"], 1)
        self.assertEqual(result["decisions_to_review"][0]["evidence_status"], "observed")
        self.assertEqual(result["decisions_to_review"][0]["missing_observation_ids"], [])
        self.assertEqual(result["recommended_actions"], [])


if __name__ == "__main__":
    unittest.main()
