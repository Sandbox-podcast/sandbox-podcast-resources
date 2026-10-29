"""Independent thumbnail review scenarios; all editorial data are fixtures."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image, ImageDraw

from youtube_growth.factory import thumbnails
from youtube_growth.factory.contracts import load_config
from youtube_growth.factory.media import fingerprint
from youtube_growth.factory.store import Store


NOW = "2026-10-28T10:00:00+01:00"


class ThumbnailReviewIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = load_config()
        self.config["thumbnails"] = {**self.config.get("thumbnails", {}), "width": 1280, "height": 720}
        self.source = self.root / "owned-source.mp4"
        self.source.write_bytes(b"source bytes for unit provenance fixture; no audiovisual assertion")
        self.rendered = self.root / "render.mp4"
        self.rendered.write_bytes(b"render bytes for unit provenance fixture; no audiovisual assertion")
        self.photo = self.root / "authorized-fixture.png"
        image = Image.new("RGB", (800, 500), "#417aaa")
        draw = ImageDraw.Draw(image)
        draw.rectangle((150, 100, 650, 400), fill="#ffc04d")
        draw.text((240, 220), "SYNTHETIC TEST FIXTURE", fill="black")
        image.save(self.photo)
        self.transcript = self.root / "transcript.json"
        self.quote = "Une équipe doit vérifier le résultat avant de le livrer."
        self.transcript.write_text(json.dumps({"source_sha256": fingerprint(self.source), "synthetic": True,
            "segments": [{"start": 0, "end": 60, "text": self.quote}]}), encoding="utf-8")
        self.episode = {"version": 1, "episode_id": "thumbnail-fixture", "title": "Fixture de vérification",
                        "source": str(self.source), "source_sha256": fingerprint(self.source),
                        "transcript": str(self.transcript), "source_probe": {"duration_seconds": 60}, "synthetic": True,
                        "availability": "available", "available_at": "2026-10-27T12:00:00+01:00",
                        "availability_checked_at": "2026-10-27T12:00:00+01:00", "availability_evidence": "Fixture de test",
                        "full_episode_id": "abcdefghijk", "full_episode_url": "https://www.youtube.com/watch?v=abcdefghijk",
                        "next_filming_at": "2026-10-30T10:00:00+01:00", "timezone": "Europe/Paris"}
        self.candidate = {"segment_id": "segment-thumbnail-fixture", "episode_id": self.episode["episode_id"],
                          "title": "Comment vérifier un résultat ?", "decision": "retained", "platforms": ["youtube"],
                          "rationale": "Exemple synthétique pour tester les liens entre preuves et packaging."}
        self.asset = {"asset_id": "asset-thumbnail-fixture", "episode_id": self.episode["episode_id"],
                      "segment_id": self.candidate["segment_id"], "path": str(self.rendered), "sha256": fingerprint(self.rendered),
                      "source_sha256": fingerprint(self.source), "format": "horizontal", "synthetic": True,
                      "qa_status": "needs_review", "qa": {"technical": "passed"},
                      "cuts": [{"source_start_seconds": 0, "source_end_seconds": 60}]}
        references = [{"reference_id": f"fixture-ref-{number}", "channel": f"Fixture channel {number//2}",
                       "video_url": f"https://example.invalid/fixture-video-{number}",
                       "thumbnail_url": f"https://example.invalid/fixture-thumbnail-{number}.jpg",
                       "format": "horizontal", "selection_reason": "Fixture de comparaison.",
                       "visual_observation": "Image synthétique déclarée pour le test.", "title_image_relation": "La phrase complète le titre.",
                       "takeaway": "Préserver un sujet lisible.", "limitations": "Aucune performance réelle.",
                       "observed_at": "2026-10-27T12:00:00+01:00", "synthetic": True,
                       "visually_inspected": True, "comparable_format": True} for number in range(6)]
        concepts = []
        for number, (angle, title, phrase) in enumerate((
                ("Vérification", "Comment vérifier le résultat d'un outil ?", "Avant de livrer"),
                ("Équipe", "Qui contrôle le travail produit par l'outil ?", "Une responsabilité"),
                ("Moment", "Quand vérifier un résultat avant livraison ?", "Le dernier contrôle"))):
            concepts.append({"concept_id": f"concept-{number}", "angle": angle,
                "hypothesis": f"Hypothèse synthétique distincte {number}.", "video_title": title,
                "thumbnail_text": phrase, "wording_reason": "Reprendre une réserve présente dans la fixture.",
                "title_image_complementarity": "Le titre pose la question ; l'image précise le moment du contrôle.",
                "visual_rationale": "Figure abstraite synthétique pour tester la mise en page, sans visage inventé.",
                "reference_ids": [f"fixture-ref-{number*2}"], "evidence_ids": ["fixture-evidence"],
                "image": {"kind": "authorized_photo", "path": str(self.photo), "sha256": fingerprint(self.photo),
                          "rights_evidence": "Image abstraite générée localement exclusivement pour ce test.",
                          "subject_identity": "Fixture abstraite, aucune personne.", "crop": [0, 0, 1, 1],
                          "focus_box": [.25, .2, .5, .6]},
                "image_box": [40, 120, 600, 500], "text_box": [700, 120, 500, 450]})
        self.brief = {"version": 1, "episode_id": self.episode["episode_id"], "segment_id": self.candidate["segment_id"],
                      "asset_sha256": self.asset["sha256"], "source_sha256": self.episode["source_sha256"],
                      "created_by": "fixture-builder", "audience": "Équipe fictive du test.",
                      "viewer_question": "Quand vérifier un résultat ?", "content_promise": "Comprendre la vérification avant livraison.",
                      "essential_nuance": "Aucune conclusion réelle sur un outil.", "selection_reason": "Choix de recette, sans résultat de performance.",
                      "preferred_concept_id": "concept-0", "benchmark": {"references": references}, "concepts": concepts,
                      "content_evidence": [{"evidence_id": "fixture-evidence", "quote": self.quote,
                                            "context": "Transcription synthétique du test.", "supports": "Vérification avant livraison.",
                                            "start_seconds": 0, "end_seconds": 60}]}

    def create(self):
        return thumbnails.create_bundle(self.brief, self.episode, self.candidate, self.asset,
                                         self.root / "thumbnails", self.config, now=NOW)

    def finished_brief(self):
        image = Image.new("RGB", (1280, 720), "#cf523d")
        ImageDraw.Draw(image).rectangle((0, 0, 250, 150), fill="#ffd51c")
        path = self.root / "finished.png"
        image.save(path)
        brief = copy.deepcopy(self.brief)
        for concept in brief["concepts"]:
            concept.update(art_direction="Fixture aux couleurs libres.", visual_story="Scène synthétique.",
                           typography_reason="Lettrage déjà intégré.", image_box=[0, 0, 1280, 720],
                           text_box=[30, 20, 400, 160])
            concept["image"].update(kind="finished_artwork", path=str(path), sha256=fingerprint(path),
                                    crop=[0, 0, 1, 1], focus_box=[.3, .3, .3, .3])
        return brief, path

    def test_finished_artwork_is_exported_without_brand_header_or_second_lettering(self):
        self.brief, path = self.finished_brief()
        self.episode["synthetic"] = False
        for reference in self.brief["benchmark"]["references"]:
            reference.pop("synthetic")
        bundle = self.create()
        result = Image.open(bundle["variants"][0]["thumbnail"]["path"])
        self.assertLess(sum(abs(a-b) for a, b in zip(result.getpixel((4, 4)), (255, 213, 28))), 15)
        self.assertLess(sum(abs(a-b) for a, b in zip(result.getpixel((900, 300)), (207, 82, 61))), 15)
        self.assertEqual(result.size, (1280, 720))
        reviewed = thumbnails.review_bundle(bundle, reviewer="art-reviewer", evidence="Synthetic artwork test",
                                             checks=sorted(thumbnails.CHECKS), now=NOW)
        thumbnails.validate_bundle(reviewed, asset=self.asset, require_review=True)
        Path(bundle["artifacts"][0]["path"]).write_bytes(b"replaced artwork")
        with self.assertRaises(ValueError):
            thumbnails.validate_bundle(reviewed, asset=self.asset, require_review=True)

    def test_finished_artwork_rejects_tampering_cropping_and_missing_art_direction(self):
        brief, path = self.finished_brief()
        for change in (lambda c: c["image"].update(sha256="invalid"),
                       lambda c: c["image"].update(crop=[0, 0, .8, 1]),
                       lambda c: c.update(art_direction=""),
                       lambda c: c.update(image_box=[40, 80, 1200, 600])):
            changed = copy.deepcopy(brief)
            change(changed["concepts"][0])
            with self.assertRaises(ValueError):
                thumbnails.validate_brief(changed, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_real_episode_cannot_fall_back_to_the_automatic_fixture_layout(self):
        self.episode["synthetic"] = False
        for reference in self.brief["benchmark"]["references"]:
            reference.pop("synthetic")
        with self.assertRaisesRegex(ValueError, "gabarit automatique"):
            self.create()

    def test_a_quote_cannot_be_located_inside_a_wider_transcript_cue_by_guessing(self):
        brief = copy.deepcopy(self.brief)
        brief["content_evidence"][0].update(start_seconds=2, end_seconds=8)
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_creator_identity_and_performance_winner_cannot_be_forged(self):
        bundle = self.create()
        changed = copy.deepcopy(bundle)
        changed["created_by"] = "another-creator"
        with self.assertRaises(ValueError):
            thumbnails.validate_bundle(changed)
        changed = copy.deepcopy(bundle)
        changed["performance_winner"] = "concept-0"
        with self.assertRaises(ValueError):
            thumbnails.validate_bundle(changed)

    def test_persisted_review_requires_reviewer_evidence_and_valid_date(self):
        bundle = thumbnails.review_bundle(self.create(), reviewer="independent-fixture-reviewer",
                                          evidence="Synthetic fixture inspection", checks=list(thumbnails.CHECKS), now=NOW)
        for key, value in (("reviewer", ""), ("reviewer", None), ("evidence", " "),
                           ("reviewed_at", "invalid-date"), ("reviewed_at", "2026-10-28T10:00:00")):
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(bundle)
                changed["review"][key] = value
                with self.assertRaises(ValueError):
                    thumbnails.validate_bundle(changed, require_review=True)
    def seed_store(self, store):
        from youtube_growth.factory import packaging
        store.put("episode", self.episode["episode_id"], self.episode, episode_id=self.episode["episode_id"], now=NOW)
        store.put("candidate", self.candidate["segment_id"], self.candidate, episode_id=self.episode["episode_id"], now=NOW)
        store.put("asset", self.asset["asset_id"], self.asset, episode_id=self.episode["episode_id"], now=NOW)
        pack = packaging.prepare(self.episode, self.candidate, self.asset, self.config,
                                  store.directory / "episodes" / self.episode["episode_id"] / "packs")[0]
        store.save_publication(pack, now=NOW)
        brief = self.root / "brief.json"
        brief.write_text(json.dumps(self.brief), encoding="utf-8")
        return pack, brief

    def prepare_and_review(self, store):
        from youtube_growth.factory import runtime
        pack, path = self.seed_store(store)
        runtime.prepare_thumbnails(store, self.config, pack["id"], path, now=NOW)
        reviewed = runtime.review_thumbnails(store, pack["id"], reviewer="fixture-reviewer", evidence="Attestation de recette synthétique.",
                                              checks=sorted(thumbnails.CHECKS), now=NOW)
        runtime.review(store, self.asset["asset_id"], evidence="Attestation de recette synthétique, aucun média réel.",
                       reviewer="fixture-media-reviewer", checks=["visual", "audio", "editorial", "subtitles"], now=NOW, fixture=True)
        return store.publication(reviewed["id"])

    def test_three_real_exports_have_feed_previews_and_no_claimed_performance_winner(self):
        bundle = self.create()
        self.assertEqual(len(bundle["variants"]), 3)
        self.assertIsNone(bundle["performance_winner"])
        self.assertEqual(bundle["review_status"], "needs_review")
        for variant in bundle["variants"]:
            with Image.open(variant["thumbnail"]["path"]) as image:
                self.assertEqual((image.format, image.size), ("JPEG", (1280, 720)))
            sizes = []
            for row in variant["previews"]:
                with Image.open(row["path"]) as preview:
                    sizes.append(preview.size)
            self.assertEqual(sizes, [(320, 180), (160, 90)])
        self.assertEqual(len({row["thumbnail"]["sha256"] for row in bundle["variants"]}), 3)
        with self.assertRaises(ValueError):
            thumbnails.validate_bundle(bundle, asset=self.asset, require_review=True)

    def test_review_is_independent_and_does_not_approve_the_media(self):
        bundle = self.create()
        with self.assertRaises(ValueError):
            thumbnails.review_bundle(bundle, reviewer="  FIXTURE-BUILDER  ", evidence="Fixture",
                                     checks=sorted(thumbnails.CHECKS), now=NOW)
        reviewed = thumbnails.review_bundle(bundle, reviewer="fixture-reviewer", evidence="Attestation synthétique de recette.",
                                            checks=sorted(thumbnails.CHECKS), now=NOW)
        thumbnails.validate_bundle(reviewed, asset=self.asset, require_review=True)
        self.assertEqual(self.asset["qa_status"], "needs_review")
        self.assertEqual(bundle["review_status"], "needs_review")

    def test_replaced_jpeg_or_preview_at_same_path_invalidates_review(self):
        bundle = thumbnails.review_bundle(self.create(), reviewer="fixture-reviewer", evidence="Fixture",
                                           checks=sorted(thumbnails.CHECKS), now=NOW)
        for artifact in (bundle["variants"][0]["thumbnail"], bundle["variants"][0]["previews"][1]):
            path = Path(artifact["path"])
            original = path.read_bytes()
            path.write_bytes(original+b"changed")
            with self.assertRaises(ValueError):
                thumbnails.validate_bundle(bundle, asset=self.asset, require_review=True)
            path.write_bytes(original)

    def test_title_or_chosen_concept_changed_after_review_is_rejected(self):
        reviewed = thumbnails.review_bundle(self.create(), reviewer="fixture-reviewer", evidence="Fixture",
                                             checks=sorted(thumbnails.CHECKS), now=NOW)
        for field in ("title", "selected"):
            changed = copy.deepcopy(reviewed)
            if field == "title":
                changed["variants"][0]["title"] = "Un autre titre après relecture"
            else:
                changed["selected_concept_id"] = "concept-1"
            with self.assertRaises(ValueError):
                thumbnails.validate_bundle(changed, asset=self.asset, require_review=True)

    def test_unsourced_quote_or_source_outside_the_cut_is_rejected(self):
        for change in (lambda row: row["content_evidence"][0].update(quote="La fixture ne prononce jamais cette phrase."),
                       lambda row: row["content_evidence"][0].update(start_seconds=61, end_seconds=62),
                       lambda row: row["concepts"][0]["image"].update(kind="episode_frame", source_time_seconds=61)):
            brief = copy.deepcopy(self.brief)
            change(brief)
            with self.assertRaises(ValueError):
                thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_essential_focus_cannot_be_cut_or_covered_by_text(self):
        for change in (lambda row: row["concepts"][0]["image"].update(crop=[0, 0, .3, .3]),
                       lambda row: row["concepts"][0].update(text_box=[40, 120, 600, 500])):
            brief = copy.deepcopy(self.brief)
            change(brief)
            with self.assertRaises(ValueError):
                thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_benchmark_requires_two_distinct_comparable_channels(self):
        brief = copy.deepcopy(self.brief)
        for index, row in enumerate(brief["benchmark"]["references"]):
            row["comparable_format"] = index < 2  # Two images from the same channel.
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_benchmark_visual_review_must_be_a_boolean_true(self):
        brief = copy.deepcopy(self.brief)
        brief["benchmark"]["references"][0]["visually_inspected"] = "not inspected"
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_exactly_repeated_hypotheses_are_rejected(self):
        brief = copy.deepcopy(self.brief)
        brief["concepts"][1]["hypothesis"] = brief["concepts"][0]["hypothesis"]
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_text_cannot_overlap_platform_timestamp_reserve(self):
        brief = copy.deepcopy(self.brief)
        brief["concepts"][0].update(text_box=[900, 600, 300, 80], thumbnail_text="Douter")
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)

    def test_old_benchmark_and_synthetic_benchmark_for_real_episode_are_rejected(self):
        brief = copy.deepcopy(self.brief)
        brief["benchmark"]["references"][0]["observed_at"] = "2026-01-01T12:00:00+01:00"
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(brief, self.episode, self.candidate, self.asset, self.config, now=NOW)
        with self.assertRaises(ValueError):
            thumbnails.validate_brief(self.brief, {**self.episode, "synthetic": False}, self.candidate, self.asset, self.config, now=NOW)

    def test_media_review_alone_cannot_schedule_an_unreviewed_thumbnail(self):
        from youtube_growth.factory import runtime, scheduler
        with Store(self.root / "state") as store:
            pack, path = self.seed_store(store)
            runtime.prepare_thumbnails(store, self.config, pack["id"], path, now=NOW)
            runtime.review(store, self.asset["asset_id"], evidence="Fixture uniquement.", reviewer="fixture-media-reviewer",
                           checks=["visual", "audio", "editorial", "subtitles"], now=NOW, fixture=True)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now=NOW)
            self.assertEqual(result["scheduled"], 0)
            current = store.publication(pack["id"])
            self.assertEqual(current["qa_status"], "passed")
            self.assertEqual(current["status"], "blocked")
            self.assertEqual(current["thumbnail_bundle"]["review_status"], "needs_review")
            self.assertIsNone(current.get("packaging_review"))

    def test_active_experiment_blocks_before_thumbnail_or_pack_files_are_written(self):
        from youtube_growth.factory import runtime
        with Store(self.root / "state") as store:
            pack, path = self.seed_store(store)
            experiment = {"experiment_id": "fixture-active-test", "publication_id": pack["id"],
                "hypothesis": "Comparaison de recette, aucune performance réelle.", "factor": "combination", "primary_metric": "fixture_metric",
                "observable_population": "Fixture", "stop_condition": "Fin de recette", "decision_rule": "Résultat non concluant",
                "design": "observational", "status": "active", "window_start": "2026-10-27T10:00:00+01:00",
                "window_end": "2026-10-30T10:00:00+01:00",
                "variants": [{"variant_id": "a", "hypothesis": "Fixture A"}, {"variant_id": "b", "hypothesis": "Fixture B"}]}
            store.put("experiment", experiment["experiment_id"], experiment, episode_id=self.episode["episode_id"], now=NOW)
            before = {str(file): file.read_bytes() for file in (store.directory / "episodes").rglob("*") if file.is_file()}
            with patch.object(thumbnails, "create_bundle", side_effect=AssertionError("No generation before lock check")) as create:
                with self.assertRaises(ValueError):
                    runtime.prepare_thumbnails(store, self.config, pack["id"], path, now=NOW)
            create.assert_not_called()
            with patch("youtube_growth.factory.media.render", side_effect=AssertionError("No render before lock check")) as render:
                with self.assertRaises(ValueError):
                    runtime.render_candidate(store, self.config, self.episode["episode_id"], self.candidate["segment_id"], "horizontal", now=NOW)
            render.assert_not_called()
            after = {str(file): file.read_bytes() for file in (store.directory / "episodes").rglob("*") if file.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(store.get("experiment", experiment["experiment_id"])["status"], "active")

    def test_packaging_text_change_invalidates_review_and_failure_is_isolated(self):
        from youtube_growth.factory import packaging, scheduler
        with Store(self.root / "state") as store:
            current = self.prepare_and_review(store)
            packaging.assert_reviewed(current, store.get("asset", self.asset["asset_id"]))
            current["text"] += " Texte changé après revue."
            store.save_publication(current, now=NOW)
            with self.assertRaises(ValueError):
                packaging.assert_reviewed(current, store.get("asset", self.asset["asset_id"]))
            self.config["authorized_accounts"]["x"] = ["fixture-x"]
            other = {**current, "id": "independent-x-publication", "platform": "x", "account_id": "fixture-x", "thumbnail_required": False,
                     "status": "ready", "segment_id": "another-fixture-segment"}
            store.put("candidate", other["segment_id"], {**self.candidate, "segment_id": other["segment_id"]},
                      episode_id=self.episode["episode_id"], now=NOW)
            store.save_publication(other, now=NOW)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now=NOW)
            self.assertEqual(result["blocked"], 1)
            self.assertEqual(result["scheduled"], 1)
            self.assertEqual(store.publication(current["id"])["status"], "blocked")
            self.assertEqual(store.publication(other["id"])["status"], "scheduled")

    def test_selected_thumbnail_changed_after_scheduling_is_rechecked_before_dispatch(self):
        from youtube_growth.factory import scheduler
        with Store(self.root / "state") as store:
            current = self.prepare_and_review(store)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now=NOW)
            self.assertEqual(result["scheduled"], 1)
            current = store.publication(current["id"])
            Path(current["cover"]).write_bytes(b"replaced after scheduling")
            with self.assertRaises(ValueError):
                scheduler.assert_sendable(store, self.config, current, now=NOW)

    def test_regenerating_pack_after_editorial_title_change_drops_previous_thumbnail_review(self):
        from youtube_growth.factory import packaging, runtime, scheduler
        with Store(self.root / "state") as store:
            current = self.prepare_and_review(store)
            previous_thumbnail = current["cover"]
            changed = {**self.candidate, "title": "Un angle révisé après relecture"}
            store.put("candidate", changed["segment_id"], changed, episode_id=self.episode["episode_id"], now=NOW)
            with patch("youtube_growth.factory.media.render", return_value=copy.deepcopy(self.asset)):
                runtime.render_candidate(store, self.config, self.episode["episode_id"], changed["segment_id"], "horizontal", now=NOW)
            regenerated = store.publication(current["id"])
            self.assertEqual(regenerated["title"], changed["title"])
            self.assertIsNone(regenerated.get("packaging_review"))
            self.assertIsNone(regenerated.get("thumbnail_bundle"))
            self.assertTrue(Path(previous_thumbnail).is_file())
            with self.assertRaises(ValueError):
                packaging.assert_reviewed(regenerated, store.get("asset", self.asset["asset_id"]))
            self.assertEqual(scheduler.plan(store, self.config, self.episode["episode_id"], now=NOW)["scheduled"], 0)

    def test_portable_backup_preserves_thumbnail_review_and_cache_without_original_sources(self):
        from youtube_growth.factory import backups, packaging
        state = self.root / "state"
        with Store(state) as store:
            current = self.prepare_and_review(store)
            before_revision = packaging.revision(current)
            before_bundle = current["thumbnail_bundle"]["bundle_id"]
            snapshot = self.root / "snapshot.sqlite3"
            backups.backup(store, snapshot, include_media=True)
        self.assertTrue(state.resolve().is_relative_to(self.root.resolve()))
        shutil.rmtree(state)
        for original in (self.source, self.rendered, self.transcript, self.photo):
            original.unlink()
        target = self.root / "restored"
        backups.restore(snapshot, target)
        with Store(target) as restored:
            row = restored.publication(current["id"])
            asset = restored.get("asset", self.asset["asset_id"])
            self.assertEqual(packaging.revision(row), before_revision)
            packaging.assert_reviewed(row, asset)
            bundle = row["thumbnail_bundle"]
            self.assertEqual(bundle["bundle_id"], before_bundle)
            for artifact in bundle["artifacts"]:
                self.assertEqual(fingerprint(Path(artifact["path"])), artifact["sha256"])
            brief = json.loads(Path(bundle["brief_path"]).read_text(encoding="utf-8"))
            episode = restored.get("episode", self.episode["episode_id"])
            candidate = restored.get("candidate", self.candidate["segment_id"])
            reused = thumbnails.create_bundle(brief, episode, candidate, asset,
                target / "episodes" / self.episode["episode_id"] / "thumbnails", self.config, now=NOW)
            self.assertEqual(reused["bundle_id"], before_bundle)
            self.assertEqual(reused["review_status"], "passed")


if __name__ == "__main__":
    unittest.main()
