from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from youtube_growth.factory.__main__ import main
from youtube_growth.factory.store import Store
from youtube_growth.factory import video_onboarding as onboarding

DISCOVERY = {"status": "available", "version": "0.5.7", "active_engine": "voxcpm2",
             "profiles": [{"profile_id": "f92d4b17", "name": "Lou", "kind": "clone", "language": "French",
                           "consent": "own_voice_attested", "revision": "r1", "usable_engines": ["voxcpm2", "omnivoice"]}],
             "effect_presets": [{"id": p} for p in ("broadcast", "cinematic", "podcast", "raw", "warm", "bright")]}
FRAMING = {"audience": "fans de rugby", "objective": "Revivre les tournants.", "angle": "Comment le match a basculé",
           "duration_minutes": 4, "format": "9:16", "autonomy": "editorial_review", "budget_limit": 0, "currency": "EUR"}


def framed(store, root, **extra):
    onboarding.start(store, session_id="video-test", answers={"video_type": "documentary", "topic": "La finale", **FRAMING, **extra})
    onboarding.answer(store, "video-test", {"voice_provider": "voicestudio"})
    onboarding.choose_voice(store, "video-test", DISCOVERY, profile_id="f92d4b17", confirmation="Prends ma voix.")
    return onboarding.frame_story(store, "video-test")


def text(root, name, content):
    path = Path(root) / name
    path.write_text(content, encoding="utf-8")
    return path


AGENT_CHECKS = {stage: {c: {"status": "passed"} for c, kind, _ in rows if kind == "agent"} for stage, rows in onboarding.CHECKS.items()}


class OnboardingTest(unittest.TestCase):
    def test_questions_are_progressive_and_answers_persist(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            step = onboarding.start(store, session_id="video-a")
            self.assertEqual((step["current_stage"]["id"], [q["field"] for q in step["questions"]]), ("format", ["video_type"]))
            self.assertEqual(step["questions"][0]["labels"]["commentary"], "Commentaire ou chronique")
            step = onboarding.answer(store, "video-a", {"video_type": "commentary"})
            self.assertEqual([q["field"] for q in step["questions"]], ["register"])
            step = onboarding.answer(store, "video-a", {"register": "dynamic", "topic": "La finale"})
            self.assertEqual(step["current_stage"]["id"], "framing")
            self.assertEqual(len(step["questions"]), 3)
            self.assertEqual(step["questions"][0]["recommendation"], "public curieux non spécialiste")
            self.assertIn("tone", [q["field"] for q in step["optional_questions"]])
            with self.assertRaisesRegex(ValueError, "number_out_of_range"):
                onboarding.answer(store, "video-a", {"duration_minutes": 500})
            with self.assertRaisesRegex(ValueError, "unknown_field"):
                onboarding.answer(store, "video-a", {"color": "bleu"})
            onboarding.answer(store, "video-a", {"duration_minutes": "4,5"})
            with Store(Path(directory)) as reopened:
                again = onboarding.next_step(reopened, "video-a")
                self.assertEqual(again["answers"]["duration_minutes"], 4.5)
                self.assertEqual(reopened.get("video_onboarding", "video-a")["answers"]["register"]["origin"], "user")

    def test_topic_and_voice_are_chosen_by_the_user(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            onboarding.start(store, session_id="video-b", answers={"video_type": "explainer"})
            step = onboarding.next_step(store, "video-b")
            self.assertEqual(step["current_stage"]["id"], "topic")
            self.assertIn("sandbox-youtube-trend-hunter", [s["id"] for s in step["skills"]])
            step = onboarding.propose_topics(store, "video-b", [
                {"title": "Pourquoi les batteries vieillissent", "angle": "La chimie du quotidien", "why": "Question fréquente.",
                 "skills_used": ["autopunk-media-skills/niche-video-idea-generator"]},
                {"title": "Le prix de l'électricité", "angle": "Qui fixe le tarif", "why": "Actualité."}])
            self.assertEqual(step["current_stage"]["status"], "awaiting_user")
            with self.assertRaisesRegex(ValueError, "confirmation_required"):
                onboarding.choose_topic(store, "video-b", rank=1, confirmation=" ")
            with self.assertRaisesRegex(ValueError, "unknown_skill"):
                onboarding.propose_topics(store, "video-b", [{"title": "A", "angle": "B", "why": "C", "skills_used": ["inventé"]}])
            step = onboarding.choose_topic(store, "video-b", rank=2, confirmation="Le deuxième.")
            self.assertEqual((step["answers"]["topic"], step["answers"]["angle"]), ("Le prix de l'électricité", "Qui fixe le tarif"))
            onboarding.answer(store, "video-b", {k: v for k, v in FRAMING.items() if k != "angle"})
            step = onboarding.answer(store, "video-b", {"voice_provider": "voicestudio"})
            self.assertEqual((step["current_stage"]["id"], step["decisions"][0]["kind"]), ("voice", "voice_choice"))
            with self.assertRaisesRegex(ValueError, "frame_story_first|stage_incomplete"):
                onboarding.frame_story(store, "video-b")
            step = onboarding.choose_voice(store, "video-b", DISCOVERY, profile_id="f92d4b17", confirmation="Ma voix.",
                                           pronunciations={"SANDBOX": "sand box"})
            self.assertEqual(step["voice"]["settings"]["effect_preset"], "broadcast")
            self.assertEqual(step["voice"]["pronunciations"], {"SANDBOX": "sand box"})

    def test_frame_creates_the_story_with_the_pinned_voice(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            result = framed(store, directory, tone="direct")
            story = result["story"]
            self.assertEqual((story["status"], story["brief"]["audio_workflow"]), ("framed", "voicestudio"))
            self.assertEqual(story["brief"]["speakers"]["narrator"]["voice"]["profile_id"], "f92d4b17")
            self.assertIn("Objectif : Revivre les tournants.", story["brief"]["notes"])
            self.assertTrue(result["next"]["story_framed"])
            self.assertEqual(result["next"]["current_stage"]["id"], "research")
            onboarding.answer(store, "video-test", {"tone": "posé"})
            step = onboarding.next_step(store, "video-test")
            self.assertFalse(step["story_framed"])
            self.assertEqual(step["decisions"][0]["kind"], "frame_story")
            with self.assertRaisesRegex(ValueError, "frame_story_first"):
                onboarding.record_stage(store, "video-test", "research", artifacts=[text(directory, "r.md", "Faits.")],
                                        checks=AGENT_CHECKS["research"])

    def test_stage_results_checks_and_stale_reviews(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            framed(store, directory)
            with self.assertRaisesRegex(ValueError, "previous_stage_incomplete_research"):
                onboarding.record_stage(store, "video-test", "structure", artifacts=[text(directory, "s.md", "Plan.")])
            with self.assertRaisesRegex(ValueError, "check_status_required"):
                onboarding.record_stage(store, "video-test", "research", artifacts=[text(directory, "r.md", "Faits.")])
            with self.assertRaisesRegex(ValueError, "stage_required"):
                onboarding.record_stage(store, "video-test", "research", status="not_applicable", reason="Pas besoin.")
            source = text(directory, "r.md", "Faits sourcés.")
            step = onboarding.record_stage(store, "video-test", "research", artifacts=[source], checks=AGENT_CHECKS["research"],
                                           skills_used=["autopunk-media-skills/claim-fact-checker"])
            saved = store.get("video_onboarding", "video-test")["stages"]["research"]
            self.assertEqual(saved["status"], "complete")
            self.assertNotEqual(saved["artifacts"][0]["path"], str(source.resolve()))
            source.write_text("Modifié après coup.", encoding="utf-8")
            self.assertEqual(Path(saved["artifacts"][0]["path"]).read_text(encoding="utf-8"), "Faits sourcés.")
            self.assertEqual(step["current_stage"]["id"], "structure")
            failed = {**AGENT_CHECKS["structure"], "progression": {"status": "failed", "note": "Acte 2 répétitif."}}
            step = onboarding.record_stage(store, "video-test", "structure", artifacts=[text(directory, "s.md", "Plan.")], checks=failed)
            self.assertEqual((step["current_stage"]["id"], step["current_stage"]["status"]), ("structure", "needs_revision"))
            onboarding.record_stage(store, "video-test", "structure", artifacts=[text(directory, "s.md", "Plan revu.")], checks=AGENT_CHECKS["structure"])
            words = " ".join(["mot"] * 600) + "."
            step = onboarding.record_stage(store, "video-test", "writing", artifacts=[text(directory, "w.md", words)], checks=AGENT_CHECKS["writing"])
            writing = store.get("video_onboarding", "video-test")["stages"]["writing"]
            self.assertEqual(writing["checks"]["duration_fit"]["status"], "passed")
            onboarding.record_stage(store, "video-test", "narrator_adaptation", artifacts=[text(directory, "n.md", "Texte.")],
                                    checks=AGENT_CHECKS["narrator_adaptation"])
            # A new voice keeps the first draft but invalidates the narrator adaptation.
            onboarding.choose_voice(store, "video-test", DISCOVERY, profile_id="f92d4b17", engine="omnivoice", confirmation="Essaie OmniVoice.")
            onboarding.frame_story(store, "video-test")
            statuses = {s["id"]: s["status"] for s in onboarding.next_step(store, "video-test")["stages"]}
            self.assertEqual((statuses["writing"], statuses["narrator_adaptation"]), ("complete", "stale"))
            onboarding.answer(store, "video-test", {"angle": "Un autre angle"})
            statuses = {s["id"]: s["status"] for s in onboarding.next_step(store, "video-test")["stages"]}
            self.assertEqual(statuses["research"], "stale")

    def test_changing_a_system_voice_only_invalidates_narrated_stages(self):
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            onboarding.start(store, session_id="video-sys", answers={"video_type": "explainer", "topic": "Les marées", **FRAMING,
                                                                      "voice_provider": "system", "system_voice": "Microsoft Hortense Desktop"})
            result = onboarding.frame_story(store, "video-sys")
            self.assertEqual(result["story"]["brief"]["speakers"]["narrator"]["voice"]["provider"], "system")
            for stage in ("research", "structure", "writing", "narrator_adaptation"):
                onboarding.record_stage(store, "video-sys", stage, artifacts=[text(directory, stage + ".md", "Texte prêt.")], checks=AGENT_CHECKS[stage])
            onboarding.answer(store, "video-sys", {"system_voice": "Microsoft Paul Desktop"})
            statuses = {s["id"]: s["status"] for s in onboarding.next_step(store, "video-sys")["stages"]}
            self.assertEqual((statuses["writing"], statuses["narrator_adaptation"]), ("complete", "stale"))

    def test_spoken_revision_blocks_text_that_cannot_be_read_aloud(self):
        report = onboarding.spoken_report([{"id": "u1", "text": "En 2026, 45 % des IA (selon l'INSEE) etc. voir https://x.fr"}], target_seconds=60)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["blocking_codes"], ["abbreviation", "brackets", "digits", "symbols", "url"])
        self.assertIn("acronym", report["counts"])
        clean = onboarding.spoken_report([{"id": "u1", "text": "Le match bascule à la soixantième minute. Personne ne l'avait vu venir."}])
        self.assertEqual(clean["status"], "passed")
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            with self.assertRaisesRegex(ValueError, "script_invalid"):
                onboarding._texts(text(directory, "broken.json", '{"scenes": [{"utterances": [{"text": 3}]}]}'))
            framed(store, directory)
            stages = ("research", "structure", "writing", "narrator_adaptation", "french_revision")
            for stage in stages:
                onboarding.record_stage(store, "video-test", stage, artifacts=[text(directory, stage + ".md", "Le texte est prêt.")],
                                        checks=AGENT_CHECKS[stage])
            step = onboarding.record_stage(store, "video-test", "spoken_revision", artifacts=[text(directory, "o.md", "Il reste 3 points.")],
                                           checks=AGENT_CHECKS["spoken_revision"])
            self.assertEqual(step["current_stage"]["status"], "needs_revision")
            step = onboarding.record_stage(store, "video-test", "spoken_revision", artifacts=[text(directory, "o.md", "Il reste trois points.")],
                                           checks=AGENT_CHECKS["spoken_revision"])
            self.assertEqual(step["current_stage"]["id"], "storyboard")
            self.assertEqual(step["checks"][0], {"id": "script_imported", "kind": "auto",
                                                 "label": onboarding.CHECKS["storyboard"][0][2]})
            failed = onboarding.record_stage(store, "video-test", "storyboard", checks=AGENT_CHECKS["storyboard"])
            self.assertEqual(failed["current_stage"]["status"], "needs_revision")

    def test_human_checks_need_the_users_words(self):
        automatic = {"technical_exports": {"status": "passed"}}
        agent = AGENT_CHECKS["controls"]
        pending = {c: {"status": "pending"} for c in ("listening_review", "visual_review", "editorial_validation")}
        self.assertEqual(onboarding.evaluate("controls", {**agent, **pending}, automatic)[1], "awaiting_user")
        with self.assertRaisesRegex(ValueError, "human_check_needs_confirmation:listening_review"):
            onboarding.evaluate("controls", {**agent, **pending, "listening_review": {"status": "passed"}}, automatic)
        confirmed = {c: {"status": "passed", "confirmed_by": "Lou", "evidence": "« J'ai tout écouté, c'est bon. »"} for c in pending}
        checks, state = onboarding.evaluate("controls", {**agent, **confirmed}, automatic)
        self.assertEqual((state, checks["listening_review"]["kind"]), ("complete", "human"))
        with self.assertRaisesRegex(ValueError, "agent_check_must_be_done:fact_check_final"):
            onboarding.evaluate("controls", {**agent, **confirmed, "fact_check_final": {"status": "waived"}}, automatic)
        failed = onboarding.evaluate("controls", {**agent, **confirmed}, {"technical_exports": {"status": "failed"}})
        self.assertEqual(failed[1], "needs_revision")
        with tempfile.TemporaryDirectory() as directory, Store(Path(directory)) as store:
            onboarding.start(store, session_id="video-h", answers={"video_type": "fiction", "topic": "Une nuit"})
            with self.assertRaisesRegex(ValueError, "previous_stage_incomplete_framing"):
                onboarding.record_stage(store, "video-h", "controls", checks={**agent, **confirmed})

    def test_every_routed_skill_exists_in_the_installed_catalog(self):
        for kind in onboarding.TYPES:
            for mode in ("documentary", "fiction", "mixed"):
                for size in ({"format": "16:9", "duration_minutes": 20}, {"format": "9:16", "duration_minutes": 1}):
                    answers = {"video_type": kind, "mode": mode, **size}
                    for stage in onboarding.STAGE_IDS:
                        for skill in onboarding.route(stage, answers):
                            self.assertTrue((onboarding.ROOT / skill["path"]).is_file(), skill)
        self.assertIn("screenwriting-skills/sw-story-structure",
                      [s["id"] for s in onboarding.route("structure", {"video_type": "fiction"})])
        self.assertIn("cc-skills/humaniseur-fr", [s["id"] for s in onboarding.route("french_revision", {"video_type": "documentary"})])

    def test_trend_hunter_brief_and_command_line(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = text(directory, "storytelling-brief.json", json.dumps({
                "story_id": "trend-story", "topic": "Les data centers et l'eau", "audience": "public français", "duration_minutes": 4,
                "format": "16:9", "notes": "Angle : la consommation réelle.", "documents": ["C:/sources/rapport.md"],
                "budget": {"limit": 0, "currency": "EUR"}}))
            state = str(Path(directory) / "state")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--state-dir", state, "video-onboarding", "start", "trend", "--brief", str(brief), "--set", "video_type=documentary"])
            self.assertEqual(code, 0)
            step = json.loads(output.getvalue())
            self.assertEqual((step["current_stage"]["id"], step["answers"]["topic"]), ("framing", "Les data centers et l'eau"))
            with Store(Path(state)) as store:
                self.assertEqual(store.get("video_onboarding", "trend")["answers"]["topic"]["origin"], "imported_brief")
                session = store.get("video_onboarding", "trend")
                onboarding.answer(store, "trend", {k: v for k, v in FRAMING.items() if k not in {"duration_minutes", "format"}})
                onboarding.answer(store, "trend", {"voice_provider": "system"}, origin="accepted_recommendation")
                onboarding.answer(store, "trend", {"system_voice": "Microsoft Hortense Desktop"})
                brief_value = onboarding.build_brief(store.get("video_onboarding", "trend"))
            self.assertEqual((brief_value["story_id"], brief_value["documents"]), ("trend-story", ["C:/sources/rapport.md"]))
            self.assertIn("Angle : la consommation réelle.", brief_value["notes"])
            self.assertEqual(session["imported_brief"]["story_id"], "trend-story")
            spoken = text(directory, "texte.md", "# Titre\n\nUn paragraphe propre.\n\nUn second, avec 12 % de 3 €.")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--state-dir", state, "video-onboarding", "spoken-check", str(spoken), "--target-minutes", "1"]), 0)
            report = json.loads(output.getvalue())
            self.assertEqual((report["units"], report["blocking_codes"]), (2, ["digits", "symbols"]))
            # A text answer that looks like JSON stays text; lists are JSON.
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--state-dir", state, "video-onboarding", "answer", "trend", "--set", "objective=2026",
                                       "--set", 'sources=["C:/sources/notes.md"]', "--set", "duration_minutes=3,5"]), 0)
            answers = json.loads(output.getvalue())["answers"]
            self.assertEqual((answers["objective"], answers["sources"], answers["duration_minutes"]), ("2026", ["C:/sources/notes.md"], 3.5))
            with Store(Path(state)) as store, self.assertRaisesRegex(ValueError, "number_out_of_range"):
                onboarding.start(store, brief={"topic": "Sans plafond", "budget": {"currency": "EUR"}})


if __name__ == "__main__":
    unittest.main()
