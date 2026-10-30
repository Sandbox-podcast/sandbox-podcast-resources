"""Real loopback HTTP tests and immutable manual-pack revisions."""
from __future__ import annotations

import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import re
import socket
import tempfile
import threading
import unittest
from urllib.parse import quote

from youtube_growth.factory import packaging, scheduler, web
from youtube_growth.factory.contracts import instant, load_config
from youtube_growth.factory.store import Store


def episode(identity: str) -> dict:
    return {"episode_id": identity, "title": "Émission "+identity, "source_sha256": "source-"+identity,
            "availability": "available", "available_at": "2026-10-28T08:00:00+01:00",
            "availability_checked_at": "2026-10-28T08:01:00+01:00", "availability_evidence": "fixture_only",
            "next_filming_at": "2026-10-30T19:00:00+01:00", "timezone": "Europe/Paris",
            "full_episode_id": "AbCdEfGhI12", "full_episode_url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
            "synthetic": True}


class LiveHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "state"
        self.config = load_config()
        with Store(self.directory) as store:
            for identity in ("episode-a", "episode-b"):
                store.put("episode", identity, episode(identity), episode_id=identity)
                store.put("candidate", "segment-"+identity, {"segment_id": "segment-"+identity}, episode_id=identity)
            for identity, ep, platform in (("publication-a-youtube", "episode-a", "youtube"),
                                            ("publication-a-x", "episode-a", "x"),
                                            ("publication-b-youtube", "episode-b", "youtube")):
                store.save_publication({"id": identity, "episode_id": ep, "platform": platform,
                                        "account_id": "configured-test-account", "asset_id": "asset-a",
                                        "title": identity, "status": "ready"})
        self.server = web.make_server(self.directory, self.config, port=0)
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.01), daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, method: str, path: str, *, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def token(self) -> str:
        code, headers, content = self.request("GET", "/")
        self.assertEqual(code, 200)
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        match = re.search(r'const token=("[0-9a-f]+");', content.decode("utf-8"))
        self.assertIsNotNone(match)
        return json.loads(match[1])

    def action(self, value: dict, *, token=None):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Factory-Token"] = token
        return self.request("POST", "/api/action", body=json.dumps(value), headers=headers)

    def test_state_filters_use_persistent_episode_and_platform(self):
        code, _, content = self.request("GET", "/api/state?episode_id=episode-a&platform=youtube")
        self.assertEqual(code, 200)
        value = json.loads(content)
        self.assertEqual([e["episode_id"] for e in value["episodes"]], ["episode-a"])
        self.assertEqual([p["id"] for p in value["publications"]], ["publication-a-youtube"])
        self.assertEqual([c["segment_id"] for c in value["candidates"]], ["segment-episode-a"])
        self.assertEqual(value["mode"], "simulation")
        self.assertFalse(value["live_enabled"])
        with Store(self.directory) as store:
            row = store.publication("publication-a-youtube")
            row["status"] = "blocked"
            store.save_publication(row)
        _, _, latest = self.request("GET", "/api/state?episode_id=episode-a&platform=youtube")
        self.assertEqual(json.loads(latest)["publications"][0]["status"], "blocked")

    def test_missing_or_wrong_csrf_token_cannot_pause_the_database(self):
        for token in (None, "invalid-token"):
            code, _, _ = self.action({"action": "pause"}, token=token)
            self.assertEqual(code, 403)
        with Store(self.directory) as store:
            self.assertFalse(store.setting("paused", False))
            self.assertEqual(store.db.execute("SELECT count(*) FROM events WHERE kind='ui_queue_pause'").fetchone()[0], 0)

    def test_storytelling_page_and_authenticated_framing(self):
        code, _, page = self.request("GET", "/storytelling")
        self.assertEqual(code, 200)
        self.assertIn("StoryTelling Generator", page.decode("utf-8"))
        body = json.dumps({"topic": "Sujet de recette", "notes": "Données fournies"})
        code, _, _ = self.request("POST", "/api/storytelling", body=body,
                                  headers={"Content-Type": "application/json"})
        self.assertEqual(code, 403)
        code, _, _ = self.request("POST", "/api/storytelling", body=body,
                                  headers={"Content-Type": "application/json", "X-Factory-Token": self.token(),
                                           "Origin": "https://example.com"})
        self.assertEqual(code, 403)
        code, _, result = self.request("POST", "/api/storytelling", body=body,
                                       headers={"Content-Type": "application/json", "X-Factory-Token": self.token()})
        self.assertEqual(code, 200)
        story = json.loads(result)
        self.assertEqual(story["production_status"], "needs_framing")
        code, _, result = self.request("GET", "/api/storytelling")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(result)["stories"][0]["story_id"], story["story_id"])

    def test_storytelling_page_lists_guided_videos_and_voice_studio_state(self):
        from youtube_growth.factory.video_onboarding import start
        with Store(self.directory) as store:
            start(store, session_id="video-ui", answers={"video_type": "documentary", "topic": "Sujet guidé"})
        code, _, page = self.request("GET", "/storytelling")
        self.assertIn("Je veux créer une nouvelle vidéo", page.decode("utf-8"))
        self.assertIn('value="voicestudio"', page.decode("utf-8"))
        code, _, result = self.request("GET", "/api/storytelling")
        row = json.loads(result)["onboarding"][0]
        self.assertEqual((row["session_id"], row["topic"], row["current_stage"]), ("video-ui", "Sujet guidé", "framing"))
        # Nothing listens on this port: the page reports Voice Studio as unavailable instead of failing.
        closed = socket.socket()
        closed.bind(("127.0.0.1", 0))
        port = closed.getsockname()[1]
        closed.close()
        self.config["voicestudio"] = {"base_url": f"http://127.0.0.1:{port}"}
        code, _, result = self.request("GET", "/api/voicestudio")
        self.assertEqual((code, json.loads(result)["status"]), (200, "unavailable"))

    def test_pause_and_resume_persist_across_http_connections(self):
        token = self.token()
        code, _, _ = self.action({"action": "pause"}, token=token)
        self.assertEqual(code, 200)
        with Store(self.directory) as store:
            self.assertTrue(store.setting("paused"))
        _, _, content = self.request("GET", "/api/state")
        self.assertTrue(json.loads(content)["paused"])
        code, _, _ = self.action({"action": "resume"}, token=token)
        self.assertEqual(code, 200)
        with Store(self.directory) as store:
            self.assertFalse(store.setting("paused"))
            self.assertEqual(store.db.execute("SELECT count(*) FROM events WHERE kind IN ('ui_queue_pause','ui_queue_resume')").fetchone()[0], 2)

    def test_unknown_dispatch_cannot_be_retried_from_the_ui(self):
        with Store(self.directory) as store:
            row = store.publication("publication-a-youtube")
            row["status"] = "unknown"
            store.save_publication(row)
            identity = store.enqueue("dispatch", "episode-a", {"publication_id": row["id"]})
            # A blocked local job must still refuse the uncertain publication.
            store.db.execute("UPDATE jobs SET status='blocked' WHERE id=?", (identity,))
        code, _, content = self.action({"action": "retry", "job_id": identity}, token=self.token())
        self.assertEqual(code, 400)
        self.assertIn("renvoi", json.loads(content)["error"])
        with Store(self.directory) as store:
            self.assertEqual(store.publication(row["id"])["status"], "unknown")
            self.assertEqual(store.jobs()[0]["status"], "blocked")

    def test_failed_local_compute_job_can_be_retried(self):
        with Store(self.directory) as store:
            identity = store.enqueue("process", "episode-a", {"revision": "fixture-revision"})
            store.db.execute("UPDATE jobs SET status='failed',attempts=3,last_error='FixtureError' WHERE id=?", (identity,))
        code, _, _ = self.action({"action": "retry", "job_id": identity}, token=self.token())
        self.assertEqual(code, 200)
        with Store(self.directory) as store:
            job = store.jobs()[0]
            self.assertEqual((job["status"], job["attempts"], job["last_error"]), ("queued", 0, None))

    def test_media_stream_range_support_and_invalid_ranges(self):
        path = self.directory / "fixture.mp4"
        content = b"0123456789fixture-media"
        path.write_bytes(content)
        with Store(self.directory) as store:
            store.put("asset", "asset-a", {"asset_id": "asset-a", "path": str(path)}, episode_id="episode-a")
        code, headers, actual = self.request("GET", "/media/asset-a", headers={"Range": "bytes=2-7"})
        self.assertEqual(code, 206)
        self.assertEqual(actual, content[2:8])
        self.assertEqual(headers["Content-Range"], f"bytes 2-7/{len(content)}")
        self.assertEqual(headers["Accept-Ranges"], "bytes")
        code, _, actual = self.request("GET", "/media/asset-a", headers={"Range": "bytes=10-"})
        self.assertEqual((code, actual), (206, content[10:]))
        code, _, actual = self.request("GET", "/media/asset-a")
        self.assertEqual((code, actual), (200, content))
        for interval in ("bytes=80-90", "bytes=8-2", "bytes=one-two", "bytes=1-2,4-5"):
            with self.subTest(interval=interval):
                code, _, _ = self.request("GET", "/media/asset-a", headers={"Range": interval})
                self.assertEqual(code, 416)

    def test_media_only_uses_registered_in_storage_paths(self):
        secret = self.root / "outside.mp4"
        secret.write_bytes(b"outside-media-must-not-be-served")
        unregistered = self.directory / "unregistered.mp4"
        unregistered.write_bytes(b"unregistered-media-must-not-be-served")
        with Store(self.directory) as store:
            store.put("asset", "outside-asset", {"asset_id": "outside-asset", "path": str(secret)})
        code, _, content = self.request("GET", "/media/outside-asset")
        self.assertEqual(code, 403)
        self.assertNotIn(secret.read_bytes(), content)
        for path in ("/media/"+quote("../outside.mp4", safe=""), "/media/unregistered.mp4", "/media/%252e%252e%252foutside.mp4"):
            with self.subTest(path=path):
                code, _, content = self.request("GET", path)
                self.assertEqual(code, 404)
                self.assertNotIn(b"must-not-be-served", content)

    def test_filtered_export_is_downloadable_and_preserves_filter_catalog(self):
        code, headers, content = self.request("GET", "/api/export?episode_id=episode-a&platform=youtube")
        self.assertEqual(code, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        value = json.loads(content)
        self.assertEqual([e["episode_id"] for e in value["episodes"]], ["episode-a"])
        self.assertEqual([p["id"] for p in value["publications"]], ["publication-a-youtube"])
        self.assertEqual({e["episode_id"] for e in value["episode_catalog"]}, {"episode-a", "episode-b"})
        self.assertEqual(value["context"]["state_directory"], str(self.directory.resolve()))
        self.assertFalse(value["live_enabled"])

    def test_valid_token_does_not_authorize_foreign_host_or_origin(self):
        token = self.token()
        for forbidden in ({"Host": "attacker.example"}, {"Origin": "https://attacker.example"}):
            headers = {"Content-Type": "application/json", "X-Factory-Token": token, **forbidden}
            code, _, _ = self.request("POST", "/api/action", body=json.dumps({"action": "pause"}), headers=headers)
            self.assertEqual(code, 403)
        with Store(self.directory) as store:
            self.assertFalse(store.setting("paused", False))

    def test_malformed_action_bodies_are_rejected_without_changing_state(self):
        token = self.token()
        bodies = [[], None, {"action": []}, {"action": None}, {"action": 123},
                  {"action": "retry", "job_id": []}, {"action": "retry", "job_id": None},
                  {"action": "retry", "job_id": 123}]
        for value in bodies:
            with self.subTest(value=value):
                code, _, content = self.action(value, token=token)
                self.assertEqual(code, 400)
                self.assertIn("error", json.loads(content))
        headers = {"Content-Type": "application/json", "X-Factory-Token": token}
        for body in ('{"action":"pause","number":NaN}', '{"action":'):
            code, _, _ = self.request("POST", "/api/action", body=body, headers=headers)
            self.assertEqual(code, 400)
        with Store(self.directory) as store:
            self.assertFalse(store.setting("paused", False))

    def test_foreign_host_is_refused_before_state_or_token_is_returned(self):
        for path in ("/", "/api/state"):
            code, _, content = self.request("GET", path, headers={"Host": "attacker.example"})
            self.assertEqual(code, 403)
            self.assertNotIn(b"const token=", content)
            self.assertNotIn(b"episodes", content)


class ManualPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = load_config()
        self.episode = episode("episode-a")
        self.candidate = {"segment_id": "segment-reviewed", "title": "Explication sourcée", "rationale": "Conséquence concrète pour une équipe.", "platforms": ["linkedin"]}

    def asset(self, revision: int):
        path = self.root / f"asset-{revision}.mp4"
        path.write_bytes(f"immutable-video-revision-{revision}".encode())
        return {"asset_id": f"asset-{revision}", "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "format": "vertical", "qa_status": "passed"}

    def prepare(self, asset, candidate=None):
        return packaging.prepare(self.episode, candidate or self.candidate, asset, self.config, self.root / "packs")[0]

    def test_new_asset_revision_preserves_old_linkedin_video_and_manifest(self):
        first = self.prepare(self.asset(1))
        first_dir = Path(first["manual_pack"])
        first_manifest = (first_dir / "pack.json").read_bytes()
        first_video = (first_dir / "video.mp4").read_bytes()
        second_asset = self.asset(2)
        second = self.prepare(second_asset)
        self.assertEqual(first["id"], second["id"])
        self.assertNotEqual(first["manual_pack"], second["manual_pack"])
        self.assertEqual((first_dir / "pack.json").read_bytes(), first_manifest)
        self.assertEqual((first_dir / "video.mp4").read_bytes(), first_video)
        self.assertEqual((Path(second["manual_pack"]) / "video.mp4").read_bytes(), Path(second_asset["path"]).read_bytes())

    def test_text_revision_preserves_the_previously_delivered_pack(self):
        asset = self.asset(1)
        first = self.prepare(asset)
        first_dir = Path(first["manual_pack"])
        initial_text = (first_dir / "texte.txt").read_bytes()
        initial_manifest = (first_dir / "pack.json").read_bytes()
        corrected = {**self.candidate, "packaging": {"linkedin": {"text": "Texte corrigé avec sa réserve explicite."}}}
        second = self.prepare(asset, corrected)
        self.assertEqual(first["id"], second["id"])
        self.assertNotEqual(first["manual_pack"], second["manual_pack"])
        self.assertEqual((first_dir / "texte.txt").read_bytes(), initial_text)
        self.assertEqual((first_dir / "pack.json").read_bytes(), initial_manifest)
        self.assertIn("réserve explicite", (Path(second["manual_pack"]) / "texte.txt").read_text(encoding="utf-8"))

    def test_planning_updates_manual_pack_date_and_keeps_linkedin_out_of_dispatch(self):
        pack = self.prepare(self.asset(1))
        with Store(self.root / "state") as store:
            store.put("episode", self.episode["episode_id"], self.episode, episode_id=self.episode["episode_id"])
            store.put("candidate", self.candidate["segment_id"], {**self.candidate, "episode_id": self.episode["episode_id"], "decision": "retained"}, episode_id=self.episode["episode_id"])
            store.save_publication(pack)
            result = scheduler.plan(store, self.config, self.episode["episode_id"], now="2026-10-28T08:00:00Z")
            row = store.publication(pack["id"])
            exported = json.loads((Path(pack["manual_pack"]) / "pack.json").read_text(encoding="utf-8"))
            self.assertEqual(result["scheduled"], 1)
            self.assertEqual(row["status"], "manual_ready")
            self.assertEqual(exported["scheduled_at"], row["scheduled_at"])
            self.assertEqual(exported["embargo_at"], self.episode["available_at"])
            self.assertEqual(exported["valid_until"], result["finish_before"])
            self.assertGreaterEqual(instant(row["scheduled_at"]), instant(self.episode["available_at"]))
            self.assertLess(instant(row["scheduled_at"]), instant(self.episode["next_filming_at"]))
            self.assertFalse(any(job["kind"] == "dispatch" for job in store.jobs()))


if __name__ == "__main__":
    unittest.main()
