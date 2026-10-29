"""Synthetic invariants, transport fixtures and a real local FFmpeg smoke render."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave
from urllib.parse import parse_qs, urlparse

from youtube_growth.trend_hunter.core import config, key, signal, stamp, write_json
from youtube_growth.trend_hunter.connectors import HTTP, YouTube, parse_feed
from youtube_growth.trend_hunter.detection import cluster, independent_support, rank, video_metrics
from youtube_growth.trend_hunter.elevenlabs import generate
from youtube_growth.trend_hunter.production import fingerprint, import_voice, prepare
from youtube_growth.trend_hunter.reporting import markdown
from youtube_growth.trend_hunter.runtime import analyze, demo
from youtube_growth.trend_hunter.store import Store

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def video(identifier, *, views=100, age=24, channel="ch-a", kind="long", at=NOW, role="candidate"):
    return signal("youtube", "OpenAI Codex nouvel outil", "https://www.youtube.com/watch?v="+identifier,
                  at-timedelta(hours=age), at, video_id=identifier, channel_id=channel, channel="Chaîne synthétique", format=kind,
                  language="fr", duration_seconds=240 if kind == "long" else 45, role=role,
                  metrics={"views": views, "likes": None, "comments": None})


def editorial_fixture(directory):
    # All content and verification are explicitly synthetic; no real announcement is asserted.
    texts = [
        "Cette démonstration présente un outil fictif nommé Atelier. Nous utilisons un sujet inventé pour vérifier le passage du dossier de recherche au scénario. Le texte que tu entends sert uniquement au contrôle local. Il ne décrit aucun produit disponible. Le schéma affiche le nom de la séquence et une phrase courte. Les fichiers de travail restent sur cet ordinateur. Nous pouvons ainsi observer la mise en page sans télécharger de photographie ni reprendre une vidéo publiée par une autre chaîne.",
        "Le dossier contient une source synthétique et une affirmation qui renvoie à cette source. Le programme vérifie que la citation apparaît dans le fichier archivé. Il contrôle aussi son empreinte. Ce contrôle permet de retrouver le document utilisé pendant la préparation. Une citation présente dans un fichier ne prouve pas que son auteur dit vrai. Dans un sujet réel, le rédacteur doit encore lire les documents primaires et expliquer ce qu'ils confirment. Cette étape reste distincte du calcul des tendances.",
        "Le montage associe les schémas à une piste audio locale. La durée de chaque séquence dépend du nombre de mots de sa narration. Ce découpage fournit une première version. Il faudra écouter la voix et corriger les sous-titres si leurs temps sont approximatifs. Lorsque la narration fournit des repères par caractère, le moteur peut les utiliser pour afficher le texte. Les images originales évitent de devoir réutiliser les plans d'un concurrent. Leur contenu doit toujours correspondre aux faits du scénario.",
        "Nous avons maintenant les éléments nécessaires au contrôle de cette démonstration. Le fichier vidéo conserve une piste audio et une image horizontale. Son reçu indique les empreintes des fichiers utilisés. Il distingue le décodage technique de la revue à l'écoute. Aucun résultat de cette démonstration ne mesure l'intérêt d'une audience. Pour préparer un sujet réel, il faut remplacer ces textes par une recherche vérifiée, une narration précise et des visuels adaptés. Le programme ne publie aucun fichier sur YouTube."
    ]
    source = directory / "source.txt"
    source.write_text("\n\n".join(texts), encoding="utf-8")
    dossier = {"version": 1, "sources": [{"source_id": "s1", "title": "Fixture synthétique", "url": "https://example.org/fixture", "kind": "primary", "rights": "Fixture originale synthétique", "retrieved_at": stamp(NOW), "snapshot": str(source), "sha256": fingerprint(source)}],
               "claims": [{"claim_id": "c1", "text": "Démonstration fictive.", "kind": "fact", "references": [{"source_id": "s1", "quote": texts[0]}], "verification": {"status": "confirmed", "reviewer": "fixture synthétique", "reason": "Test du contrat uniquement", "checked_at": stamp(NOW)}}]}
    write_json(directory / "dossier.json", dossier)
    editorial = {"research_dossier": "dossier.json", "angle": "Démonstration synthétique", "titles": ["Démonstration locale", "Vérifier un montage local", "Du texte au rendu de test"], "description": "Démonstration synthétique, aucune actualité réelle.", "thumbnail": "Schéma original sur fond sombre.",
                 "scenes": [{"role": "hook" if i == 0 else "conclusion" if i == 3 else "development", "heading": "Démonstration synthétique "+str(i+1), "narration": text, "on_screen": "Contrôle local, données fictives", "visual": "Carte typographique originale", "statement_kind": "fact", "claim_ids": ["c1"]} for i, text in enumerate(texts)]}
    path = directory / "editorial.json"
    write_json(path, editorial)
    return path


class TrendHunterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "state")
        self.cfg = config()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_current_quota_buckets_and_pacific_reset(self):
        self.store.reserve("search", 1, NOW)
        with self.assertRaises(RuntimeError):
            self.store.reserve("search", 1, NOW)
        self.store.reserve("other", 2, NOW)
        self.assertEqual(self.store.quotas(NOW), {"search": 1, "other": 1})
        # 06:30 UTC is still the previous Pacific date in October.
        self.store.reserve("search", 1, NOW.replace(hour=6))
        self.assertEqual(self.store.quotas(NOW.replace(hour=6)), {"search": 1})

    def test_cache_keeps_original_observation_time_and_reserves_before_failure(self):
        calls = []
        @contextmanager
        def opener(req, timeout):
            calls.append(req.full_url)
            yield BytesIO(b'{"items": []}')
        client = HTTP(self.store, self.cfg, NOW, opener=opener)
        yt = YouTube(client, self.cfg, "secret-key")
        first = yt.call("search", part="snippet", q="codex")
        client.now = NOW+timedelta(minutes=5)
        second = yt.call("search", part="snippet", q="codex")
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.store.quotas(NOW)["search"], 1)
        dump = "".join(self.store.db.iterdump())
        self.assertNotIn("secret-key", dump)
        def failure(req, timeout):
            raise TimeoutError()
        client.opener = failure
        with self.assertRaises(RuntimeError):
            yt.call("videos", id="new-id")
        self.assertEqual(self.store.quotas(NOW)["other"], 1)

    def test_http_blocks_paid_hosts_and_limits_requests(self):
        client = HTTP(self.store, self.cfg, NOW)
        for url in ("https://api.openai.com/v1/responses", "https://api.anthropic.com/v1/messages", "http://news.google.com/rss", "https://localhost/rss"):
            with self.assertRaises(ValueError):
                client.get(url)
        client.requests = self.cfg["http"]["max_requests_per_run"]
        with self.assertRaises(RuntimeError):
            client.get("https://news.google.com/rss")

    def test_rss_does_not_invent_volume_date_or_reddit_engagement(self):
        xml = '<rss xmlns:ht="https://trends.google.com/trending/rss"><channel><item><title>Codex &amp; agents</title><link>https://example.org/a</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate><ht:approx_traffic>20K+</ht:approx_traffic></item><item><title>Sans date</title><link>https://example.org/b</link></item></channel></rss>'
        rows = parse_feed(xml, "trends", NOW, region="FR")
        self.assertEqual(rows[0]["metrics"], {"approx_traffic_text": "20K+"})
        self.assertIsNone(rows[1]["published_at"])
        atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Discussion Codex</title><link href="https://www.reddit.com/r/a/comments/1/"/><updated>2026-10-29T10:00:00Z</updated></entry></feed>'
        self.assertEqual(parse_feed(atom, "reddit", NOW)[0]["metrics"], {})

    def test_trends_items_sharing_feed_link_keep_distinct_identifiers(self):
        xml = '<rss><channel><item><title>Codex</title><link>https://trends.google.com/trending/rss?geo=FR</link></item><item><title>Gemini</title><link>https://trends.google.com/trending/rss?geo=FR</link></item></channel></rss>'
        rows = parse_feed(xml, "trends", NOW, region="FR")
        self.store.observe(rows)
        self.assertEqual(len(self.store.latest(NOW)), 2)
        self.assertNotEqual(rows[0]["id"], rows[1]["id"])

    def test_syndicated_news_is_not_independent_or_audience_demand(self):
        rows = [signal("news", "OpenAI Codex nouvel outil", f"https://example.org/{i}", NOW, NOW, publisher_domain=f"publisher{i}.example", language="fr") for i in range(4)]
        self.assertEqual(len(independent_support(rows)), 1)
        accepted, rejected = rank(rows, self.store, self.cfg, NOW, [])
        self.assertFalse(accepted)
        self.assertIn("news_only_without_audience_signal", rejected[0]["reasons"])
        xml = '<rss><channel><item><title>OpenAI Codex - Journal</title><link>https://news.google.com/rss/articles/1</link><source url="https://journal.example">Journal</source></item></channel></rss>'
        self.assertEqual(parse_feed(xml, "news", NOW)[0]["title"], "OpenAI Codex")

    def test_youtube_short_format_unknown_and_hidden_stats_missing(self):
        class Transport:
            def get(self, url, **kwargs):
                return json.dumps({"items": [{"id": "shortvideo1", "snippet": {"title": "Un clip", "channelId": "ch", "channelTitle": "Channel", "publishedAt": stamp(NOW-timedelta(hours=1))}, "statistics": {"viewCount": "50"}, "contentDetails": {"duration": "PT2M"}}]}), stamp(NOW)
        row = YouTube(Transport(), self.cfg, "key").videos(["shortvideo1"])[0]
        self.assertEqual(row["format"], "unknown_short_or_long")
        self.assertIsNone(row["metrics"]["likes"])
        self.assertIsNone(row["metrics"]["comments"])

    def test_youtube_dual_search_batch_details_channel_history_and_scoring(self):
        calls = []
        @contextmanager
        def opener(req, timeout):
            parsed = urlparse(req.full_url)
            endpoint = parsed.path.rsplit("/", 1)[-1]
            params = parse_qs(parsed.query)
            calls.append((endpoint, params))
            if endpoint == "search":
                identifier = "candidate01" if params["relevanceLanguage"] == ["fr"] else "candidate02"
                items = [{"id": {"videoId": identifier}}]
            elif endpoint == "channels":
                items = [{"id": "ch-a", "snippet": {"title": "Fixture"}, "statistics": {"videoCount": "7", "hiddenSubscriberCount": True}, "contentDetails": {"relatedPlaylists": {"uploads": "uploads-a"}}}]
            elif endpoint == "playlistItems":
                items = [{"contentDetails": {"videoId": "baseline00"+str(i)}} for i in range(5)]
            else:
                items = [{"id": identifier, "snippet": {"title": "OpenAI Codex nouvel outil", "channelId": "ch-a", "channelTitle": "Fixture", "defaultAudioLanguage": "fr" if identifier != "candidate02" else "en", "publishedAt": stamp(NOW-timedelta(hours=24))},
                          "statistics": {"viewCount": "150000" if identifier.startswith("candidate") else "10000"}, "contentDetails": {"duration": "PT4M"}} for identifier in params["id"][0].split(",")]
            yield BytesIO(json.dumps({"items": items}).encode())
        cfg = deepcopy(self.cfg)
        cfg["youtube"].update(search_topics=1, channels_per_run=1, baseline_videos=5)
        youtube = YouTube(HTTP(self.store, cfg, NOW, opener=opener), cfg, "fixture-key")
        rows, errors = youtube.collect(["OpenAI Codex"], self.store)
        self.assertFalse(errors)
        self.assertEqual(len(rows), 7)
        self.assertEqual(len(youtube.search_samples), 2)
        self.assertEqual(self.store.quotas(NOW), {"search": 2, "other": 4})
        self.assertNotIn("subscriberCount", youtube.channels["ch-a"]["statistics"])
        self.store.observe(rows)
        candidate = next(r for r in rows if r["video_id"] == "candidate01")
        self.assertEqual(video_metrics(candidate, self.store, cfg)["outperformance_ratio"], 15)
        self.assertEqual(sum(endpoint == "videos" for endpoint, _ in calls), 2)

    def test_median_age_matched_baseline_and_formats_are_separate(self):
        current = video("current0001", views=150000)
        references = [video("base000000"+str(i), views=v, age=23+i*.1) for i, v in enumerate((9000, 10000, 10000, 11000, 900000))]
        references += [video("short000001", views=1, kind="unknown_short_or_long"), video("old00000001", views=1, age=500)]
        self.store.observe([current, *references])
        result = video_metrics(current, self.store, self.cfg)
        self.assertEqual(result["outperformance_ratio"], 15)
        self.assertEqual(result["baseline_count"], 5)
        self.assertEqual(result["baseline_median"], 10000)
        self.assertIsNone(video_metrics(references[-2], self.store, self.cfg)["outperformance_ratio"])

    def test_velocity_requires_two_samples_acceleration_three(self):
        v = video("current0001", views=100, age=20, at=NOW-timedelta(hours=4))
        self.store.observe([v])
        result = video_metrics(v, self.store, self.cfg)
        self.assertEqual(result["average_views_per_hour"], 5)
        self.assertIsNone(result["interval_views_per_hour"])
        self.assertIsNone(result["acceleration_ratio"])
        second = {**v, "observed_at": stamp(NOW-timedelta(hours=2)), "metrics": {"views": 300}}
        third = {**v, "observed_at": stamp(NOW), "metrics": {"views": 900}}
        self.store.observe([second])
        self.assertEqual(video_metrics(second, self.store, self.cfg)["interval_views_per_hour"], 100)
        self.assertIsNone(video_metrics(second, self.store, self.cfg)["acceleration_ratio"])
        self.store.observe([third])
        self.assertEqual(video_metrics(third, self.store, self.cfg)["acceleration_ratio"], 3)

    def test_duplicate_topics_and_cross_language_alias(self):
        rows = [signal("news", t, "https://example.org/"+str(i), NOW, NOW) for i, t in enumerate(("OpenAI Codex arrive en France", "OpenAI Codex arrive enfin en France", "OpenAI releases Codex in France"))]
        groups = cluster(rows, {"Codex France": ["OpenAI Codex", "Codex in France"]})
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["signals"]), 3)

    def test_ranking_missing_data_repeat_filter_and_sensitive_exclusion(self):
        report, directory = demo(self.store, self.cfg, now=NOW)
        self.assertEqual(len(report["opportunities"]), 1)
        row = report["opportunities"][0]
        self.assertIsNone(row["components"]["outperformance"])
        self.assertEqual(row["contributions"]["outperformance"], 0)
        self.assertEqual(row["confidence"], "Faible")
        self.assertTrue(markdown(report).startswith("| Rang |"))
        self.assertIn("SYNTHÉTIQUE", markdown(report))
        self.assertEqual(self.store.run()["run_id"], report["run_id"])
        rows = row["evidence"]
        accepted, rejected = rank(rows, self.store, self.cfg, NOW+timedelta(hours=1), [])
        self.assertFalse(accepted)
        self.assertIn("recently_recommended_without_material_change", rejected[0]["reasons"])
        dangerous = [{**r, "title": "OpenAI conseil traitement cancer", "id": key(r["id"]+"sensitive")} for r in rows]
        self.assertFalse(rank(dangerous, self.store, self.cfg, NOW, [])[0])

    def test_failure_of_all_sources_produces_empty_honest_report_without_key(self):
        class FailingHTTP:
            requests = 0
            now = NOW
            def get(self, *args, **kwargs):
                raise RuntimeError("Fixture : source indisponible")
        with patch.dict(os.environ, {}, clear=True):
            report, directory = analyze(self.store, self.cfg, now=NOW, http=FailingHTTP())
        self.assertEqual(report["opportunities"], [])
        self.assertFalse(report["synthetic"])
        self.assertEqual(report["source_status"]["youtube"]["status"], "no_key")
        self.assertTrue((directory / "report.json").exists())

    def test_prepare_requires_research_then_checks_snapshots_and_script(self):
        report, _ = demo(self.store, self.cfg, now=NOW)
        pending = prepare(self.store, 1, self.cfg, now=NOW)
        self.assertEqual(json.loads((pending / "pack.json").read_text())["status"], "research_required")
        with self.assertRaises(ValueError):
            import_voice(pending, self.root / "missing.mp3")
        path = editorial_fixture(self.root)
        ready = prepare(self.store, 1, self.cfg, editorial_path=path, now=NOW)
        for name in ("research.md", "script.md", "storyboard.json", "titles.md", "thumbnail.md", "description.md", "attributions.md", "assets", "audio", "render"):
            self.assertTrue((ready / name).exists(), name)
        self.assertEqual(len(list((ready / "assets").glob("*.png"))), 4)
        (self.root / "source.txt").write_text("Source modifiée", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "empreinte"):
            prepare(self.store, 1, self.cfg, editorial_path=path, now=NOW)

    def test_elevenlabs_default_never_calls_network(self):
        demo(self.store, self.cfg, now=NOW)
        path = prepare(self.store, 1, self.cfg, editorial_path=editorial_fixture(self.root), now=NOW)
        with patch("youtube_growth.trend_hunter.elevenlabs.build_opener") as opener:
            with self.assertRaises(ValueError):
                generate(path, self.cfg)
            opener.assert_not_called()

    def test_elevenlabs_unsafe_subscription_prevents_post_and_failed_post_cannot_retry(self):
        demo(self.store, self.cfg, now=NOW)
        path = prepare(self.store, 1, self.cfg, editorial_path=editorial_fixture(self.root), now=NOW)
        cfg = deepcopy(self.cfg)
        cfg["elevenlabs"].update(enabled=True, voice_id="stock-voice")
        calls = []
        subscription = {"status": "active", "tier": "creator", "character_count": 0, "character_limit": 100000, "allowed_to_extend_character_limit": True}
        @contextmanager
        def opener(req, timeout):
            calls.append((req.method, req.full_url))
            if req.full_url.endswith("subscription"):
                yield BytesIO(json.dumps(subscription).encode())
            elif req.full_url.endswith("models"):
                yield BytesIO(json.dumps([{"model_id": "eleven_multilingual_v2", "can_do_text_to_speech": True, "maximum_text_length_per_request": 5000, "model_rates": {"character_cost_multiplier": 1, "cost_discount_multiplier": 1}}]).encode())
            elif "/voices/" in req.full_url:
                yield BytesIO(b'{"category":"premade", "available_for_tiers":["creator"]}')
            else:
                raise TimeoutError("unknown result")
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "fixture-secret"}):
            with self.assertRaisesRegex(ValueError, "Dépassement"):
                generate(path, cfg, included_credits_only=True, opener=opener)
            self.assertFalse(any(method == "POST" for method, _ in calls))
            subscription["allowed_to_extend_character_limit"] = False
            with self.assertRaises(RuntimeError):
                generate(path, cfg, included_credits_only=True, opener=opener)
            with self.assertRaisesRegex(ValueError, "tentative"):
                generate(path, cfg, included_credits_only=True, opener=opener)
        self.assertEqual(sum(method == "POST" for method, _ in calls), 1)
        self.assertNotIn("fixture-secret", (path / "audio/elevenlabs-attempt.json").read_text())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe non disponibles")
    def test_real_ffmpeg_render_synthetic_and_integrity(self):
        from youtube_growth.trend_hunter.render import render
        demo(self.store, self.cfg, now=NOW)
        path = prepare(self.store, 1, self.cfg, editorial_path=editorial_fixture(self.root), now=NOW)
        source = self.root / "synthetic-silence.wav"
        with wave.open(str(source), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(b"\0\0"*32000)
        import_voice(path, source)
        receipt = render(path, allow_demo=True)
        self.assertTrue(Path(receipt["path"]).exists())
        self.assertTrue(receipt["synthetic"])
        self.assertEqual(receipt["audiovisual_review"], "pending")
        self.assertIn("estimated", receipt["caption_accuracy"])
        self.assertEqual(receipt["sha256"], fingerprint(receipt["path"]))
        (path / "script.md").write_text("Texte modifié", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "script"):
            render(path, allow_demo=True)


if __name__ == "__main__":
    unittest.main()
