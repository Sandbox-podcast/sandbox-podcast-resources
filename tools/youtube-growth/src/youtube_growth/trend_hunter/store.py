"""Local observations, cached responses and separate quota buckets."""
from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from .core import instant, stamp


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "trends.sqlite3", timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, at TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS quotas (day TEXT, bucket TEXT, used INTEGER, PRIMARY KEY(day,bucket));
        CREATE TABLE IF NOT EXISTS observations (id TEXT, at TEXT, body TEXT, PRIMARY KEY(id,at));
        CREATE TABLE IF NOT EXISTS recommendations (topic TEXT PRIMARY KEY, at TEXT, score INTEGER);
        CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, at TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS outcomes (id INTEGER PRIMARY KEY, at TEXT, body TEXT);
        """)

    def close(self):
        self.db.close()

    def cached(self, identifier, now, ttl):
        row = self.db.execute("SELECT * FROM cache WHERE id=?", (identifier,)).fetchone()
        if row and 0 <= (instant(now)-instant(row["at"])).total_seconds() < ttl:
            return json.loads(row["body"]), row["at"]
        return None

    def cache(self, identifier, at, body):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?)", (identifier, stamp(at), json.dumps(body)))

    def reserve(self, bucket, limit, now):
        day = instant(now).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO quotas VALUES(?,?,0)", (day, bucket))
            changed = self.db.execute("UPDATE quotas SET used=used+1 WHERE day=? AND bucket=? AND used < ?", (day, bucket, limit)).rowcount
            if not changed:
                raise RuntimeError("Budget quotidien épuisé : "+bucket)

    def quotas(self, now):
        day = instant(now).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()
        return {r["bucket"]: r["used"] for r in self.db.execute("SELECT * FROM quotas WHERE day=?", (day,))}

    def observe(self, rows):
        with self.db:
            for row in rows:
                self.db.execute("INSERT OR IGNORE INTO observations VALUES(?,?,?)", (row["id"], row["observed_at"], json.dumps(row, ensure_ascii=False)))

    def history(self, identifier):
        return [json.loads(r[0]) for r in self.db.execute("SELECT body FROM observations WHERE id=? ORDER BY at", (identifier,))]

    def latest(self, since):
        return [json.loads(r[0]) for r in self.db.execute("SELECT o.body FROM observations o JOIN (SELECT id, MAX(at) at FROM observations GROUP BY id) x ON o.id=x.id AND o.at=x.at WHERE o.at>=?", (stamp(since),))]

    def baseline(self, channel_id, exclude, now):
        return [r for r in self.latest(instant(now)-timedelta(days=30)) if r["source"] == "youtube" and r.get("channel_id") == channel_id and r["id"] != exclude]

    def previous(self, topic):
        row = self.db.execute("SELECT * FROM recommendations WHERE topic=?", (topic,)).fetchone()
        return dict(row) if row else None

    def save_run(self, report):
        with self.db:
            self.db.execute("INSERT INTO runs VALUES(?,?,?)", (report["run_id"], report["collected_at"], json.dumps(report, ensure_ascii=False)))
            for topic in report["opportunities"]:
                self.db.execute("INSERT OR REPLACE INTO recommendations VALUES(?,?,?)", (topic["topic_id"], report["collected_at"], topic["score"]))

    def run(self, identifier=None):
        row = self.db.execute("SELECT body FROM runs WHERE id=?", (identifier,)).fetchone() if identifier else self.db.execute("SELECT body FROM runs ORDER BY at DESC, rowid DESC LIMIT 1").fetchone()
        if not row:
            raise ValueError("Aucune analyse ; lancer analyze d'abord.")
        return json.loads(row[0])

    def prune(self, now):
        # Public YouTube API data are refreshed on every collection and retained at most 30 days.
        cutoff = stamp(instant(now)-timedelta(days=30))
        with self.db:
            for table in ("cache", "observations", "runs"):
                self.db.execute(f"DELETE FROM {table} WHERE at < ?", (cutoff,))
        reports = self.directory / "reports"
        if reports.exists():
            for path in reports.glob("*"):
                if path.is_dir() and path.name.replace("-", "").isalnum():
                    manifest = path / "report.json"
                    if manifest.exists() and instant(json.loads(manifest.read_text(encoding="utf-8"))["collected_at"]) < instant(cutoff):
                        for filename in ("report.json", "report.md"):
                            (path / filename).unlink(missing_ok=True)
