"""A selected trend is a framing input, never approval to generate sound or a script."""
from copy import deepcopy
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from youtube_growth.trend_hunter.core import config, load_json, write_json
from youtube_growth.trend_hunter.runtime import demo
from youtube_growth.trend_hunter.store import Store
from youtube_growth.trend_hunter.storytelling import CONTRACT, check_handoff, handoff
from test_trend_hunter import NOW, editorial_fixture


class StorytellingHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "trends")
        self.addCleanup(self.store.close)
        self.cfg = config()
        self.report, _ = demo(self.store, self.cfg, now=NOW)
        editorial_fixture(self.root)
        self.arguments = {"run_id": self.report["run_id"], "selected_by": "Lou (fixture)",
                          "selection_note": "Cette tendance m'intéresse pour une vidéo.", "now": NOW}

    def export(self, **extra):
        return handoff(self.store, 1, self.cfg, **{**self.arguments, **extra})

    def test_selected_topic_produces_a_complete_framing_input_without_a_script(self):
        path, result = self.export(research_path=self.root / "dossier.json")
        brief = load_json(path / "storytelling-brief.json")
        self.assertEqual(result["status"], "ready_for_storytelling_framing")
        self.assertEqual(brief["topic"], self.report["opportunities"][0]["subject"])
        self.assertEqual(brief["duration_minutes"], 3)
        self.assertEqual(brief["mode"], "documentary")
        self.assertEqual(brief["autonomy"], "editorial_review")
        self.assertEqual(brief["budget"], {"limit": 0, "currency": "EUR", "browser_credit_limit": 0})
        self.assertEqual(brief["audio_workflow"], "elevenlabs_browser")
        self.assertEqual(brief["links"], [])
        self.assertTrue(all(Path(p).is_file() for p in brief["documents"]))
        self.assertTrue(brief["trend_origin"]["synthetic"])
        self.assertFalse(brief["trend_origin"]["script_approved"])
        self.assertFalse((path / "script.md").exists())
        self.assertFalse((path / "audio").exists())
        source_map = load_json(path / "source-map.json")
        facts = load_json(path / "research-facts.json")["facts"]
        self.assertEqual(facts[0]["source_ids"], [source_map["s1"]["source_id"]])
        self.assertEqual(facts[0]["status"], "source_supported")
        self.assertNotIn("verification", next(m for m in brief["source_metadata"].values() if m["kind"] == "primary"))
        self.assertEqual(check_handoff(path), result)

    def test_missing_research_is_explicit_and_does_not_promote_headlines_to_facts(self):
        path, result = self.export()
        self.assertEqual(result["status"], "research_required")
        self.assertEqual(load_json(path / "research-facts.json")["facts"], [])
        self.assertTrue(any("sources primaires" in q for q in result["remaining_decisions"]))
        self.assertFalse(any(m["kind"] == "primary" for m in load_json(path / "storytelling-brief.json")["source_metadata"].values()))

    def test_original_run_and_rank_are_used_after_another_collection(self):
        cfg = deepcopy(self.cfg)
        cfg["repeat_after_hours"] = 0
        later, _ = demo(self.store, cfg, now=NOW+timedelta(hours=1))
        with self.store.db:
            self.store.db.execute("UPDATE runs SET body=? WHERE id=?", (json.dumps({**later, "opportunities": []}), later["run_id"]))
        _, result = self.export()
        self.assertEqual(result["selection"]["run_id"], self.report["run_id"])
        self.assertEqual(result["selection"]["topic_id"], self.report["opportunities"][0]["topic_id"])
        with self.assertRaises(ValueError):
            self.export(run_id=later["run_id"])

    def test_repeated_export_reuses_files_and_a_change_creates_a_revision(self):
        path, first = self.export(research_path=self.root / "dossier.json")
        repeated, second = self.export(research_path=self.root / "dossier.json", now=NOW+timedelta(minutes=10))
        self.assertEqual(path, repeated)
        self.assertEqual(first, second)
        revised, third = self.export(research_path=self.root / "dossier.json", angle="Examiner le cas d'usage annoncé.")
        self.assertNotEqual(path, revised)
        self.assertEqual(first["story_id"], third["story_id"])
        self.assertEqual(check_handoff(path), first)
        voiced, voice_result = self.export(research_path=self.root / "dossier.json", voice_name="Voix choisie (fixture)", browser_credit_limit=200)
        voice_brief = load_json(voiced / "storytelling-brief.json")
        self.assertEqual(voice_brief["budget"]["browser_credit_limit"], 200)
        self.assertEqual(voice_brief["speakers"]["narrator"]["voice"]["name"], "Voix choisie (fixture)")
        self.assertFalse(voice_result["selection"]["production_started"])

    def test_selection_required_bad_budget_stale_report_and_modified_sources(self):
        for override in ({"run_id": None}, {"selected_by": ""}, {"selection_note": ""}, {"browser_credit_limit": -1}):
            with self.assertRaises(ValueError):
                self.export(**override)
        path, result = self.export(research_path=self.root / "dossier.json")
        _, old = self.export(research_path=self.root / "dossier.json", now=NOW+timedelta(days=8))
        self.assertEqual(old["status"], "research_required")
        (path / "trend-evidence.json").write_text("Modifié", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modifié"):
            self.export(research_path=self.root / "dossier.json")
        (self.root / "source.txt").write_text("Source remplacée", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "empreinte"):
            self.export(research_path=self.root / "dossier.json", angle="Autre angle.")

    def test_cli_exports_the_selected_run_without_importing_the_factory(self):
        completed = subprocess.run([sys.executable, "-m", "youtube_growth.trend_hunter", "--state-dir", str(self.store.directory),
                                    "storytelling", "1", "--run", self.report["run_id"], "--selected-by", "Lou (fixture)",
                                    "--selection-note", "Celle-ci me plaît", "--research-dossier", str(self.root / "dossier.json")],
                                   capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"), timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "ready_for_storytelling_framing")
        self.assertTrue(Path(result["brief"]).is_file())
        self.assertFalse(list(self.store.directory.rglob("factory.sqlite3")))

    def test_actual_pr19_framing_source_import_and_authoring_request(self):
        root = os.environ.get("STORYTELLING_CONTRACT_ROOT")
        if not root:
            installed = Path(__import__("youtube_growth.factory", fromlist=["__file__"]).__file__).parent / "storytelling.py"
            if installed.exists():
                root = str(installed.parents[5])
            else:
                self.skipTest("PR19 non installée ; définir STORYTELLING_CONTRACT_ROOT pour sa recette isolée.")
        path, result = self.export(research_path=self.root / "dossier.json")
        (self.root / "source.txt").unlink()  # The generator must consume the bundle's copy.
        # Load the real target package in another interpreter, keeping this branch's factory untouched.
        script = r'''
import json,sys
from pathlib import Path
from youtube_growth.factory.store import Store
from youtube_growth.factory.storytelling import frame
from youtube_growth.factory.storytelling_sources import import_sources
from youtube_growth.factory.storytelling_editorial import build_request
brief=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
with Store(Path(sys.argv[2])/'factory') as store:
 framed=frame(store,brief)
 assert framed['status']=='framed', framed['questions']
 assert framed['brief']['duration_minutes']==3
 assert framed['brief']['budget']['browser_credit_limit']==0
 imported=import_sources(framed['brief'],Path(sys.argv[2])/'imported')
 assert not imported['blockers'], imported['blockers']
 request=build_request(framed['brief'],imported)
 assert request['task']=='storytelling_complete_script'
 assert not request['brief']['trend_origin']['script_approved']
 facts=json.loads((Path(sys.argv[1]).parent/'research-facts.json').read_text(encoding='utf-8'))['facts']
 sources={s['source_id']:s for s in imported['sources']}
 for fact in facts:
  for quote in fact['quotes']:
   assert quote['quote'] in sources[quote['source_id']]['text']
 assert any(s['kind']=='primary' for s in request['untrusted_sources'])
 assert not store.jobs()
 print(json.dumps({'status':'compatible','sources':len(imported['sources'])}))
'''
        environment = dict(os.environ, PYTHONPATH=str(Path(root) / "tools/youtube-growth/src"), PYTHONUTF8="1")
        completed = subprocess.run([sys.executable, "-c", script, str(path / "storytelling-brief.json"), str(self.root / "compat")],
                                   env=environment, cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "compatible")


if __name__ == "__main__":
    unittest.main()
