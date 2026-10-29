"""Bounded public read-only collectors. No browser scraping or paid fallback."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET

from .core import instant, key, signal, stamp

HOSTS = {"trends.google.com", "news.google.com", "www.reddit.com", "hn.algolia.com", "www.googleapis.com"}


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != "https" or urlparse(newurl).hostname != urlparse(req.full_url).hostname:
            raise ValueError("Redirection du collecteur vers un autre domaine refusée.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HTTP:
    def __init__(self, store, config, now, *, opener=None):
        self.store, self.config, self.now = store, config, now
        self.opener = opener or build_opener(SafeRedirect()).open
        self.requests = 0

    def get(self, url, *, quota=None):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("URL de collecteur non autorisée.")
        identifier = key(url)  # API keys never persisted in plaintext.
        hit = self.store.cached(identifier, self.now, self.config["http"]["cache_seconds"])
        if hit:
            return hit
        if self.requests >= self.config["http"]["max_requests_per_run"]:
            raise RuntimeError("Budget HTTP de cette exécution épuisé.")
        if quota:
            self.store.reserve(*quota, self.now)
        self.requests += 1
        request = Request(url, headers={"User-Agent": "SANDBOX-TrendHunter/1.0 (public RSS research)", "Accept": "application/json, application/rss+xml, application/atom+xml, text/xml"})
        try:
            with self.opener(request, timeout=self.config["http"]["timeout_seconds"]) as response:
                body = response.read(4_000_001)
            if len(body) > 4_000_000:
                raise ValueError("Réponse trop volumineuse.")
            text = body.decode("utf-8-sig")
        except HTTPError as error:
            # Do not expose error URLs, which may contain the API key.
            raise RuntimeError(f"Collecteur {parsed.hostname} : HTTP {error.code} ; aucune reprise automatique.") from None
        except (URLError, TimeoutError, OSError):
            raise RuntimeError("Collecteur "+parsed.hostname+" indisponible ; aucun repli payant.") from None
        self.store.cache(identifier, self.now, text)
        return text, stamp(self.now)


def date(value):
    if not value:
        return None
    try:
        return stamp(value)
    except (ValueError, TypeError):
        try:
            return stamp(parsedate_to_datetime(value))
        except (ValueError, TypeError):
            return None


def clean(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def parse_feed(body, source, at, *, region=None, language=None):
    root = ET.fromstring(body)
    rows = []
    atom = {"a": "http://www.w3.org/2005/Atom"}
    for item in list(root.findall("./channel/item")) + list(root.findall("a:entry", atom)):
        title = clean(item.findtext("title") or item.findtext("a:title", namespaces=atom))
        link = item.findtext("link")
        if not link:
            element = item.find("a:link[@rel='alternate']", atom)
            if element is None:
                element = item.find("a:link", atom)
            link = element.get("href") if element is not None else None
        published = date(item.findtext("pubDate") or item.findtext("a:published", namespaces=atom) or item.findtext("a:updated", namespaces=atom))
        metrics, related = {}, []
        for child in item:
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "approx_traffic":
                metrics["approx_traffic_text"] = child.text  # Bucket, never exact volume or growth.
            if tag == "news_item":
                fields = {c.tag.rsplit("}", 1)[-1]: c.text for c in child}
                related.append({"title": clean(fields.get("news_item_title")), "url": fields.get("news_item_url")})
        publisher = item.find("source")
        publisher_url = publisher.get("url") if publisher is not None else None
        publisher_name = clean(publisher.text) if publisher is not None else None
        if publisher_name and title.endswith(" - "+publisher_name):
            title = title[:-(len(publisher_name)+3)].strip()
        if title and link and link.startswith("https://"):
            rows.append(signal(source, title, link, published, at, region=region, language=language, metrics=metrics,
                               publisher_domain=urlparse(publisher_url).hostname if publisher_url else None,
                               publisher_name=publisher_name,
                               related_news=related))
    return rows


def trends(http, cfg):
    rows, errors = [], []
    for region in cfg["regions"]:
        try:
            body, at = http.get("https://trends.google.com/trending/rss?"+urlencode({"geo": region}))
            rows.extend(parse_feed(body, "trends", at, region=region, language="fr" if region == "FR" else "en" if region == "US" else None))
        except (RuntimeError, ValueError, ET.ParseError) as error:
            errors.append(str(error))
    return rows, errors


def news(http, cfg):
    rows, errors = [], []
    for region in cfg["regions"]:
        language = "fr" if region == "FR" else "en"
        params = {"hl": language, "gl": region, "ceid": f"{region}:{language}"}
        if cfg["mode"] == "ai-tech":
            params["q"] = cfg["news_queries"][language]+f" when:{cfg['window_days']}d"
        url = "https://news.google.com/rss"+("/search" if "q" in params else "")+"?"+urlencode(params)
        try:
            body, at = http.get(url)
            rows.extend(parse_feed(body, "news", at, region=region, language=language))
        except (RuntimeError, ValueError, ET.ParseError) as error:
            errors.append(str(error))
    return rows, errors


def reddit(http, cfg):
    rows, errors = [], []
    for community in cfg["reddit_communities"]:
        try:
            body, at = http.get(f"https://www.reddit.com/r/{community}/hot/.rss?limit=25")
            rows.extend(parse_feed(body, "reddit", at))
        except (RuntimeError, ValueError, ET.ParseError) as error:
            errors.append(str(error))
    return rows, errors


def hackernews(http, cfg):
    since = int((instant(http.now)-timedelta(days=cfg["window_days"])).timestamp())
    params = {"tags": "story", "numericFilters": f"created_at_i>{since},points>20", "hitsPerPage": 50}
    if cfg["mode"] == "ai-tech":
        params["query"] = "AI"
    body, at = http.get("https://hn.algolia.com/api/v1/search_by_date?"+urlencode(params))
    rows = []
    for item in json.loads(body).get("hits", []):
        rows.append(signal("hackernews", clean(item.get("title")), f"https://news.ycombinator.com/item?id={item['objectID']}",
                           date(item.get("created_at")), at, language="en", article_url=item.get("url"),
                           metrics={"points": item.get("points"), "comments": item.get("num_comments")}))
    return rows, []


def duration(value):
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", value or "")
    return sum(float(x or 0)*m for x, m in zip(match.groups(), (3600, 60, 1))) if match else None


class YouTube:
    def __init__(self, http, cfg, api_key):
        self.http, self.cfg, self.api_key = http, cfg, api_key
        self.search_samples, self.channels, self.errors = [], {}, []

    def call(self, endpoint, **params):
        budget = ("search", self.cfg["youtube"]["daily_search_calls"]) if endpoint == "search" else ("other", self.cfg["youtube"]["daily_other_units"])
        body, at = self.http.get("https://www.googleapis.com/youtube/v3/"+endpoint+"?"+urlencode({**params, "key": self.api_key}), quota=budget)
        result = json.loads(body)
        if "error" in result:
            raise RuntimeError("YouTube a refusé la lecture ; vérifier la clé et les quotas.")
        return result.get("items", []), at

    def videos(self, identifiers, *, role="candidate"):
        rows = []
        ids = sorted(set(identifiers))
        for offset in range(0, len(ids), 50):
            items, at = self.call("videos", part="snippet,statistics,contentDetails", id=",".join(ids[offset:offset+50]), maxResults=50)
            for item in items:
                snippet, stats = item["snippet"], item.get("statistics", {})
                seconds = duration(item.get("contentDetails", {}).get("duration"))
                # Data API has no reliable isShort flag or orientation. Ambiguous clips remain separate.
                kind = "long" if seconds and seconds > 180 else "unknown_short_or_long"
                lang = snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage")
                rows.append(signal("youtube", snippet["title"], "https://www.youtube.com/watch?v="+item["id"], snippet["publishedAt"], at,
                                   video_id=item["id"], channel_id=snippet["channelId"], channel=snippet["channelTitle"],
                                   language=lang.split("-")[0] if lang else None, duration_seconds=seconds, format=kind,
                                   format_basis="duration_over_180s" if kind == "long" else "api_cannot_confirm_shorts",
                                   description=snippet.get("description", ""), category_id=snippet.get("categoryId"), role=role,
                                   metrics={name: int(stats[field]) if field in stats else None for name, field in (("views", "viewCount"), ("likes", "likeCount"), ("comments", "commentCount"))}))
        return rows

    def collect(self, topics, store):
        found = set()
        after = stamp(instant(self.http.now)-timedelta(days=self.cfg["window_days"]))
        for title in topics[:self.cfg["youtube"]["search_topics"]]:
            for lang, region in (("fr", "FR"), ("en", "US")):
                try:
                    items, at = self.call("search", part="snippet", type="video", q=title, publishedAfter=after,
                                          order="viewCount", relevanceLanguage=lang, regionCode=region, maxResults=25)
                    ids = [r["id"]["videoId"] for r in items]
                    found.update(ids)
                    self.search_samples.append({"query": title, "language_hint": lang, "region": region, "observed_at": at,
                                                "ids": ids, "limit": 25, "complete_census": False})
                except (RuntimeError, ValueError) as error:
                    self.errors.append(str(error))
        tracked = [r["video_id"] for r in store.latest(instant(self.http.now)-timedelta(days=30)) if r["source"] == "youtube"]
        found.update(tracked[:self.cfg["youtube"]["refresh_videos"]])
        rows = []
        try:
            rows = self.videos(found)
        except (RuntimeError, ValueError) as error:
            self.errors.append(str(error))
        channels = list(dict.fromkeys(r["channel_id"] for r in rows))[:self.cfg["youtube"]["channels_per_run"]]
        if channels:
            try:
                items, at = self.call("channels", part="contentDetails,statistics,snippet", id=",".join(channels))
                baseline_ids = set()
                for item in items:
                    stats = item.get("statistics", {})
                    self.channels[item["id"]] = {"observed_at": at, "title": item["snippet"]["title"],
                                                  "statistics": {k: int(v) if str(v).isdigit() else v for k, v in stats.items()}}
                    playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]
                    try:
                        uploads, _ = self.call("playlistItems", part="contentDetails", playlistId=playlist, maxResults=self.cfg["youtube"]["baseline_videos"])
                        baseline_ids.update(r["contentDetails"]["videoId"] for r in uploads)
                    except (RuntimeError, ValueError) as error:
                        self.errors.append(str(error))
                rows.extend(self.videos(baseline_ids-found, role="baseline"))
            except (RuntimeError, ValueError) as error:
                self.errors.append(str(error))
        return rows, self.errors


COLLECTORS = {"trends": trends, "news": news, "reddit": reddit, "hackernews": hackernews}
