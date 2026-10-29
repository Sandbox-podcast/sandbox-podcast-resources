"""Editorial, research and narrative boundaries using temporary local fixtures."""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from youtube_growth.factory import editorial, research, narrative, media, analytics
from youtube_growth.factory.contracts import digest, load_config
from youtube_growth.factory.store import Store
from youtube_growth.factory.editorial_runtime import assess

NOW = "2026-10-29T13:00:00Z"


def candidate(key="one", start=0, end=35):
    return {"segment_id": key, "title": "La latence des agents vocaux", "source_sha256": "a"*64,
            "decision": "needs_review", "cuts": [{"source_start_seconds": start, "source_end_seconds": end}]}


def judgment(row, **changes):
    value = {"candidate_sha256": digest(row), "reviewer": "fixture-agent", "assessed_at": NOW,
        "criteria": {k: {"score": 80, "reason": "Motif de recette", "evidence": ["fixture:0..35"]} for k in editorial.CRITERIA},
        "rationale": "Discussion avec un exemple", "angle": "L'attente ressentie", "hook": "Dix secondes d'attente",
        "viewer_benefit": "Comprendre les étapes", "topic_key": "latence-vocale", "format": "short",
        "format_reason": "Une idée autonome", "standalone": True, "hook_at_seconds": 0, "blockers": []}
    value.update(changes)
    return value


class EditorialTests(unittest.TestCase):
    def test_no_judgment_never_becomes_heuristic_selection(self):
        row = editorial.evaluate(candidate(), None, now=NOW)
        self.assertIsNone(row["score"])
        self.assertEqual(row["recommended_format"], "none")

    def test_no_quota_and_same_topic_is_not_produced_twice(self):
        a, b = candidate(), candidate("two", 60, 90)
        value = editorial.rank([a, b], {"one": judgment(a), "two": judgment(b)}, now=NOW)
        self.assertEqual(sum(r["status"] == "recommended" for r in value["opportunities"]), 1)
        self.assertIsNone(value["quota"])
        self.assertEqual(editorial.rank([], {}, now=NOW)["opportunities"], [])

    def test_format_uses_cut_duration_instead_of_source_span(self):
        row = candidate(end=20)
        row["cuts"].append({"source_start_seconds": 600, "source_end_seconds": 620})
        self.assertEqual(editorial.evaluate(row, judgment(row), now=NOW)["recommended_format"], "short")
        self.assertIn("edit_duration_outside_format", editorial.evaluate(row, judgment(row, format="extract"), now=NOW)["blockers"])

    def test_hard_blocker_overrides_score_and_future_judgment_is_refused(self):
        row = candidate()
        result = editorial.evaluate(row, judgment(row, hook_at_seconds=3), now=NOW)
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["recommended_format"], "none")
        with self.assertRaises(ValueError):
            editorial.evaluate(row, judgment(row, assessed_at="2027-01-01T00:00:00Z"), now=NOW)

    def test_stale_judgment_and_nan_are_refused(self):
        row = candidate()
        changed = {**row, "title": "Autre titre"}
        with self.assertRaises(ValueError):
            editorial.evaluate(changed, judgment(row), now=NOW)
        value = judgment(row)
        value["criteria"]["curiosity"]["score"] = float("nan")
        with self.assertRaises(ValueError):
            editorial.evaluate(row, value, now=NOW)

    def test_export_does_not_erase_previous_judgment(self):
        with tempfile.TemporaryDirectory() as tmp, Store(Path(tmp)/"state") as store:
            row = candidate()
            store.put("episode", "episode", {"title": "fixture"}, episode_id="episode")
            store.put("candidate", "one", row, episode_id="episode")
            supplied = Path(tmp)/"judgments.json"
            supplied.write_text(json.dumps({"judgments": {"one": judgment(row)}}), encoding="utf-8")
            assess(store, load_config(), episode_id="episode", judgments_path=supplied, now=NOW)
            assess(store, load_config(), episode_id="episode", now=NOW)
            self.assertEqual(store.get("opportunity", "one")["score"], 80)
            self.assertEqual(store.get("candidate", "one")["decision"], "needs_review")


def dossier(root):
    snapshot = root/"source.txt"
    snapshot.write_text("Speech can be processed incrementally.", encoding="utf-8")
    return {"version": 1, "sources": [{"source_id": "official", "title": "Fixture officielle", "kind": "primary",
        "url": "https://example.org/docs", "snapshot": str(snapshot), "sha256": media.fingerprint(snapshot),
        "retrieved_at": NOW, "rights": "Citation technique de recette"}],
        "claims": [{"claim_id": "incremental", "kind": "fact", "text": "Traitement progressif",
        "references": [{"source_id": "official", "quote": "processed incrementally"}],
        "verification": {"status": "confirmed", "reviewer": "fixture", "reason": "Citation exacte", "checked_at": NOW}}]}


def story(root):
    (root/"research.json").write_text(json.dumps(dossier(root)), encoding="utf-8")
    beats = [{"beat_id": key, "role": role, "narration": "Phrase de test.", "heading": "Une scène",
              "claim_ids": ["incremental"], "statement_kind": "fact", "visual": {"type": "flow", "labels": ["Entrée", "Sortie"]}}
             for key, role in (("opening", "hook"), ("ending", "conclusion"))]
    return {"version": 1, "story_id": "fixture-story", "title": "Fixture", "research": "research.json", "angle": "Expliquer",
        "audience": "Développeurs", "sandbox_analysis": "Hypothèse de test", "beats": beats,
        "voice": {"provider": "system", "name": "fixture", "cloned": False, "authorization": "voix standard"},
        "metadata": {"titles": ["Titre A", "Titre B", "Titre C"], "description": "Description de recette",
            "thumbnail_concepts": [{"hypothesis": str(i), "composition": "Schéma", "text": "Mot", "evidence": "incremental"} for i in range(3)]}}


class ResearchNarrativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_unverified_fact_blocks_script_and_invented_quote_is_rejected(self):
        value = dossier(self.root)
        value["claims"][0]["verification"]["status"] = "pending"
        self.assertEqual(research.verify(value, now=NOW)["status"], "blocked")
        value["claims"][0]["references"][0]["quote"] = "invented causal claim"
        with self.assertRaises(ValueError):
            research.verify(value, now=NOW)

    def test_analysis_cannot_be_relabelled_as_confirmed_fact(self):
        data = story(self.root)
        verified = research.verify(dossier(self.root), now=NOW)
        verified["claims"][0]["kind"] = "analysis"
        with self.assertRaises(ValueError):
            narrative.validate_script(data, verified)

    def test_stage_cache_and_snapshot_integrity_before_cache_hit(self):
        path = self.root/"story.json"
        path.write_text(json.dumps(story(self.root)), encoding="utf-8")
        with Store(self.root/"state") as store:
            one = narrative.run(store, load_config(), path, stage="storyboard", now=NOW)
            two = narrative.run(store, load_config(), path, stage="storyboard", now=NOW)
            self.assertEqual(one["revision"], two["revision"])
            self.assertTrue(all(x["cache"] == "hit" for x in two["stages"].values()))
            (self.root/"source.txt").write_text("modified", encoding="utf-8")
            with self.assertRaises(ValueError):
                narrative.run(store, load_config(), path, stage="storyboard", now=NOW)

    def test_portrait_has_its_own_composition_and_no_cloned_voice(self):
        data = story(self.root)
        script = narrative.validate_script(data, research.verify(dossier(self.root), now=NOW))
        a, b = narrative.storyboard(script, "horizontal"), narrative.storyboard(script, "vertical")
        self.assertNotEqual(a["scenes"][0]["composition"], b["scenes"][0]["composition"])
        with self.assertRaises(ValueError):
            narrative.voice(a, {"cloned": True, "provider": "system"}, self.root/"voice", base=self.root)

    def test_technical_pronunciations_preserve_original_captions(self):
        self.assertEqual(narrative.spoken("Un LLM, puis du TTS.", {"LLM": "èle èle ème", "TTS": "té té esse"}),
                         "Un èle èle ème, puis du té té esse.")

    def test_transcript_support_allows_draft_but_preserves_oral_gap(self):
        data = dossier(self.root)
        data["sources"][0]["kind"] = "episode"
        data["claims"][0]["kind"] = "testimony"
        data["claims"][0]["verification"]["status"] = "transcript_supported"
        value = research.verify(data, now=NOW)
        self.assertEqual(value["status"], "ready_for_script")
        self.assertFalse(value["claims"][0]["verified"])
        self.assertEqual(value["oral_verification_pending"], ["incremental"])

    def test_voice_is_shared_after_title_or_aspect_ratio_change(self):
        data = story(self.root)
        path = self.root/"story.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with Store(self.root/"state") as store, patch.object(narrative, "voice", return_value={"duration_seconds": 200, "artifacts": []}) as synth:
            narrative.run(store, load_config(), path, stage="voice", now=NOW)
            data["title"] = "Titre corrigé"
            path.write_text(json.dumps(data), encoding="utf-8")
            narrative.run(store, load_config(), path, stage="voice", format_name="vertical", now=NOW)
            self.assertEqual(synth.call_count, 1)

    def test_targeted_rerun_preserves_later_completed_stages(self):
        data = story(self.root)
        path = self.root/"story.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with Store(self.root/"state") as store:
            first = narrative.run(store, load_config(), path, stage="storyboard", now=NOW)
            second = narrative.run(store, load_config(), path, stage="research", now=NOW)
            self.assertEqual(set(first["stages"]), set(second["stages"]))

    def _complete_fixture(self, store, data):
        path = self.root/"story.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        output = self.root/"fixture-video.mp4"
        output.write_bytes(b"local unit fixture, not a real video")
        sound = {"duration_seconds": 200, "artifacts": [], "scenes": [
            {"beat_id": b["beat_id"], "start_seconds": i*100} for i,b in enumerate(data["beats"])]}
        asset = {"path": str(output), "sha256": media.fingerprint(output),
                 "artifacts": [{"path": str(output), "sha256": media.fingerprint(output)}]}
        with patch.object(narrative, "voice", return_value=sound), \
                patch("youtube_growth.factory.narrative_visuals.render", return_value=asset):
            return narrative.run(store, load_config(), path, now=NOW), path, output

    def test_partial_rerun_refuses_a_modified_previously_approved_video(self):
        data = story(self.root)
        with Store(self.root/"state") as store:
            result, path, output = self._complete_fixture(store, data)
            record_id = result["story_id"]+":"+result["revision"]
            narrative.review(store, record_id, reviewer="fixture", evidence="Unit fixture only",
                checks=["facts", "editorial", "visual", "audio", "subtitles", "packaging"], now=NOW)
            output.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "artefact narratif"):
                narrative.run(store, load_config(), path, stage="research", now=NOW)

    def test_final_review_rechecks_research_expiration(self):
        data = story(self.root)
        dossier_path = self.root/"research.json"
        evidence = json.loads(dossier_path.read_text(encoding="utf-8"))
        evidence["expires_at"] = "2026-10-29T14:00:00Z"
        dossier_path.write_text(json.dumps(evidence), encoding="utf-8")
        with Store(self.root/"state") as store:
            result, _, _ = self._complete_fixture(store, data)
            with self.assertRaisesRegex(ValueError, "research_expired"):
                narrative.review(store, result["story_id"]+":"+result["revision"], reviewer="fixture", evidence="Unit fixture only",
                    checks=["facts", "editorial", "visual", "audio", "subtitles", "packaging"], now="2026-10-29T15:00:00Z")

    def test_narrative_backup_contains_sources_and_resumes_after_restore(self):
        from youtube_growth.factory.backups import backup, restore
        data = story(self.root)
        path = self.root/"story.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        snapshot = self.root/"snapshot.sqlite3"
        with Store(self.root/"state") as store:
            first = narrative.run(store, load_config(), path, stage="storyboard", now=NOW)
            backup(store, snapshot, include_media=True)
        target = self.root/"restored"
        restore(snapshot, target)
        with Store(target) as store:
            restored = store.records("narrative")[0]
            self.assertTrue(Path(restored["resume_story_path"]).is_relative_to(target))
            result = narrative.run(store, load_config(), Path(restored["resume_story_path"]), stage="storyboard", now=NOW)
            self.assertEqual(result["status"], "prepared")
            backup(store, self.root/"second-snapshot.sqlite3", include_media=True)

    def test_final_review_refuses_transcript_only_testimony(self):
        data = story(self.root)
        dossier_data = json.loads((self.root/"research.json").read_text(encoding="utf-8"))
        dossier_data["sources"][0]["kind"] = "episode"
        dossier_data["claims"][0].update(kind="testimony", verification={"status": "transcript_supported", "reviewer": "fixture", "reason": "Texte seulement", "checked_at": NOW})
        (self.root/"research.json").write_text(json.dumps(dossier_data), encoding="utf-8")
        for beat in data["beats"]:
            beat["statement_kind"] = "testimony"
        path = self.root/"story.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        sound = {"duration_seconds": 200, "artifacts": [], "scenes": [{"beat_id": b["beat_id"], "start_seconds": i*100} for i,b in enumerate(data["beats"])]}
        with Store(self.root/"state") as store, patch.object(narrative, "voice", return_value=sound), \
                patch("youtube_growth.factory.narrative_visuals.render", return_value={"sha256": "a"*64, "artifacts": []}):
            result = narrative.run(store, load_config(), path, now=NOW)
            with self.assertRaisesRegex(ValueError, "Témoignage"):
                narrative.review(store, result["story_id"]+":"+result["revision"], reviewer="fixture", evidence="Fixture",
                    checks=["facts", "editorial", "visual", "audio", "subtitles", "packaging"], now=NOW)

    def test_frames_move_and_portrait_is_not_a_crop(self):
        from youtube_growth.factory.narrative_visuals import frame
        from PIL import ImageChops
        scene = story(self.root)["beats"][0]
        speech = {"duration_seconds": 10, "sentences": []}
        a = frame(scene, speech, .1, (960, 540))
        b = frame(scene, speech, 3, (960, 540))
        self.assertIsNotNone(ImageChops.difference(a, b).getbbox())
        self.assertEqual(frame(scene, speech, 3, (540, 960)).size, (540, 960))

    def test_reorder_requires_review_and_no_overlap(self):
        value = {"cuts": [{"source_start_seconds": 20, "source_end_seconds": 30},
                           {"source_start_seconds": 0, "source_end_seconds": 10}]}
        with self.assertRaises(ValueError):
            media._cuts(value, 100)
        value["edit_order_review"] = {"reviewer": "fixture", "reason": "Contexte compréhensible", "evidence": "fixture", "preserves_meaning": True}
        self.assertEqual(media._cuts(value, 100)[-1]["output_end_seconds"], 20)
        value["cuts"][1].update(source_start_seconds=25, source_end_seconds=35)
        with self.assertRaises(ValueError):
            media._cuts(value, 100)


class ModelAdapterTests(unittest.TestCase):
    def test_local_protocol_cache_and_cost_guard(self):
        from youtube_growth.factory.generation import generate
        with tempfile.TemporaryDirectory() as tmp:
            config = {"generation": {"local_command": [sys.executable, "-c", "import json,sys; print(json.dumps({'echo': json.load(sys.stdin)}))"],
                                     "network": False, "cost_per_call": 0, "model_revision": "fixture-1"}}
            value = generate({"test": 1}, config, Path(tmp))
            self.assertEqual(value["echo"], {"test": 1})
            with patch("subprocess.run", side_effect=AssertionError("cache miss")):
                self.assertEqual(generate({"test": 1}, config, Path(tmp)), value)
            config["generation"]["cost_per_call"] = 1
            with self.assertRaises(ValueError):
                generate({"test": 1}, config, Path(tmp))


class CohortTests(unittest.TestCase):
    def test_comparable_content_and_no_causal_winner(self):
        from test_factory_analytics import observation
        contexts, rows = [], []
        for key, duration, count in (("a", 200, 1000), ("b", 210, 1400), ("c", 700, 1000)):
            contexts.append({"entity_id": key, "format": "narrative", "duration_seconds": duration,
                "published_at": "2026-10-01T00:00:00Z", "topic": "agents", "hook": key, "visual_style": "diagram", "provenance": "fixture"})
            for metric, value in (("impressions", count), ("averageViewPercentage", 60)):
                rows.append(observation(observation_id=key+metric, entity_id=key, metric=metric, value=value,
                    period_start="2026-10-01T00:00:00Z", period_end="2026-10-22T00:00:00Z", collected_at="2026-10-23T00:00:00Z"))
        result = analytics.compare_content(rows, contexts, now=NOW)
        self.assertTrue(result["cohorts"])
        self.assertTrue(all(c["causal_winner"] is None for c in result["cohorts"]))
        self.assertTrue(all(len(c["members"]) == 2 for c in result["cohorts"]))
        self.assertTrue(any(r["reason"] == "no_comparable_peer" for r in result["excluded"]))

    def test_missing_impressions_and_synthetic_cannot_drive_recommendations(self):
        from test_factory_analytics import observation
        rows = [observation(), observation(observation_id="fixture", data_class="synthetic_fixture")]
        value = analytics.compare_content(rows, [], now=NOW)
        self.assertEqual(value["cohorts"], [])
        self.assertEqual(value["synthetic_excluded"], 1)

    def test_retention_positions_are_separate_series(self):
        from test_factory_analytics import observation
        rows = [observation(observation_id=str(i), metric="audienceWatchRatio", value=.8,
                            dimensions={"elapsedVideoTimeRatio": i/10}) for i in (1, 5)]
        self.assertEqual(len(analytics.summarize(rows)["series"]), 2)


class DiscoveryImportTests(unittest.TestCase):
    def test_discovery_reads_all_text_and_refuses_invented_hook(self):
        from youtube_growth.factory.editorial_runtime import discover
        with tempfile.TemporaryDirectory() as tmp, Store(Path(tmp)/"state") as store:
            root = Path(tmp)
            transcript = root/"transcript.json"
            transcript.write_text(json.dumps({"segments": [{"start": 0, "end": 20, "text": "Un agent répond après une attente."},
                {"start": 20, "end": 40, "text": "On mesure chaque étape."}]}), encoding="utf-8")
            store.put("episode", "ep", {"transcript": str(transcript), "source_sha256": "a"*64}, episode_id="ep")
            store.put("analysis", "ep", {"duration_seconds": 40}, episode_id="ep")
            response = {"candidates": [{"title": "Une attente", "audience": "Développeurs", "rationale": "Mesurer", "angle": "Localiser",
                        "cuts": [{"source_start_seconds": 0, "source_end_seconds": 40}],
                        "hook_evidence": {"quote": "Un agent répond", "start_seconds": 0, "end_seconds": 2}}]}
            proposals = root/"proposals.json"
            proposals.write_text(json.dumps(response), encoding="utf-8")
            result = discover(store, load_config(), "ep", proposals_path=proposals, now=NOW)
            self.assertEqual(result["proposals"][0]["decision"], "needs_review")
            request = json.loads(Path(result["request_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(request["segments"]), 2)
            self.assertEqual(store.records("candidate"), [])
            response["candidates"][0]["hook_evidence"]["quote"] = "Paroles inventées"
            proposals.write_text(json.dumps(response), encoding="utf-8")
            with self.assertRaises(ValueError):
                discover(store, load_config(), "ep", proposals_path=proposals, now=NOW)

    def test_import_keeps_retention_dimensions_and_reuses_ids(self):
        from youtube_growth.factory.analytics_import import import_audit
        config = load_config()
        audit = {"identity_verified": True, "channel": {"id": config["authorized_accounts"]["youtube"][0]},
            "video": {"id": "example"}, "captured_at": NOW, "period": {"start": "2026-10-20", "end": "2026-10-21"},
            "analytics": {"retention": {"status": "available", "data": {"columns": ["elapsedVideoTimeRatio", "audienceWatchRatio"],
                           "rows": [[.1, .8], [.5, .6]]}}}}
        with tempfile.TemporaryDirectory() as tmp, Store(Path(tmp)) as store:
            result = import_audit(store, config, audit, fixture=True, now=NOW)
            import_audit(store, config, audit, fixture=True, now=NOW)
            self.assertEqual(len(store.records("observation")), 2)
            self.assertEqual(result["data_class"], "synthetic_fixture")
            self.assertEqual(len(analytics.summarize(store.records("observation"))["series"]), 2)
            self.assertIn("impressions", result["missing_metrics"])

    def test_queue_uses_existing_worker_and_does_not_send(self):
        from youtube_growth.factory import runtime
        with tempfile.TemporaryDirectory() as tmp, Store(Path(tmp)/"state") as store:
            root = Path(tmp)
            source = root/"story.json"
            source.write_text("{}", encoding="utf-8")
            store.set_setting("last_collection_at", NOW)
            store.set_setting("last_report_at", NOW)
            store.enqueue("narrative", None, {"story_path": str(source), "story_sha256": media.fingerprint(source),
                "stage": "storyboard", "format": "horizontal", "draft": True}, now=NOW)
            with patch.object(runtime, "watch", return_value={}), patch.object(narrative, "run", return_value={"status": "prepared"}) as execute:
                result = runtime.run_once(store, load_config(), now=NOW)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(execute.call_count, 1)
            self.assertEqual(store.publications(), [])

    def test_worker_records_a_blocked_narrative_as_blocked(self):
        from youtube_growth.factory import runtime
        with tempfile.TemporaryDirectory() as tmp, Store(Path(tmp)/"state") as store:
            source = Path(tmp)/"story.json"
            source.write_text("{}", encoding="utf-8")
            store.set_setting("last_collection_at", NOW)
            store.set_setting("last_report_at", NOW)
            job_id = store.enqueue("narrative", None, {"story_path": str(source), "story_sha256": media.fingerprint(source),
                "stage": "all", "format": "horizontal", "draft": True}, now=NOW)
            with patch.object(runtime, "watch", return_value={}), patch.object(narrative, "run", return_value={"status": "blocked"}):
                result = runtime.run_once(store, load_config(), now=NOW)
            self.assertEqual(result["status"], "blocked")
            job = next(j for j in store.jobs() if j["id"] == job_id)
            self.assertEqual(job["status"], "blocked")
            self.assertEqual(job["last_error"], "narrative_research_blocked")


@unittest.skipUnless(os.environ.get("FACTORY_MEDIA_INTEGRATION") == "1", "Recette média explicite requise")
class NarrativeMediaIntegrationTests(unittest.TestCase):
    def test_real_animated_scene_encode_decode_and_immutable_receipt(self):
        from youtube_growth.factory.narrative_visuals import render
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/"fixture.wav"
            with wave.open(str(path), "wb") as target:
                target.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                target.writeframes(b"".join(struct.pack("<h", round(3000*math.sin(2*math.pi*440*i/24000))) for i in range(24000)))
            scene = {"beat_id": "fixture", "role": "hook", "narration": "Recette synthétique.", "heading": "Fixture synthétique",
                     "statement_kind": "analysis", "visual": {"type": "flow", "labels": ["Entrée", "Sortie"]}}
            audio = {"duration_seconds": 1, "scenes": [{"beat_id": "fixture", "path": str(path), "sha256": media.fingerprint(path),
                      "start_seconds": 0, "duration_seconds": 1, "sentences": [{"caption": "Recette synthétique.", "start_seconds": 0, "end_seconds": 1}]}]}
            value = render({"format": "horizontal", "scenes": [scene]}, audio, root/"render", load_config(), draft=True)
            self.assertEqual(value["qa"]["technical"]["decode"], "passed")
            self.assertAlmostEqual(value["duration_seconds"], 1, delta=.2)
            Path(value["path"]).write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                render({"format": "horizontal", "scenes": [scene]}, audio, root/"render", load_config(), draft=True)


if __name__ == "__main__":
    unittest.main()
