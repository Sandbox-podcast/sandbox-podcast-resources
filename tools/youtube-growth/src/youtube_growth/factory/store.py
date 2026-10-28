"""SQLite is the execution source of truth; input manifests are imported revisions."""
from __future__ import annotations

from contextlib import contextmanager, closing
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
import uuid

from .contracts import digest, iso, instant, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS records(kind TEXT NOT NULL,id TEXT NOT NULL,episode_id TEXT,
 data TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(kind,id));
CREATE INDEX IF NOT EXISTS records_episode ON records(episode_id,kind);
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,kind TEXT NOT NULL,episode_id TEXT,
 payload TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,
 due_at TEXT NOT NULL,lease_until TEXT,owner TEXT,last_error TEXT);
CREATE INDEX IF NOT EXISTS jobs_due ON jobs(status,due_at);
CREATE TABLE IF NOT EXISTS publications(id TEXT PRIMARY KEY,episode_id TEXT NOT NULL,
 platform TEXT NOT NULL,account_id TEXT NOT NULL,asset_id TEXT NOT NULL,status TEXT NOT NULL,
 scheduled_at TEXT,remote_id TEXT,data TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 kind TEXT NOT NULL,entity_id TEXT,data TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
"""


class Store:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "factory.sqlite3"
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def event(self, kind: str, entity_id: str | None, data: dict, *, now=None):
        self.db.execute("INSERT INTO events(kind,entity_id,data,created_at) VALUES(?,?,?,?)",
                        (kind, entity_id, json.dumps(data, ensure_ascii=False, allow_nan=False), iso(now or utcnow())))

    def put(self, kind: str, identity: str, data: dict, *, episode_id=None, now=None):
        self.db.execute("INSERT INTO records VALUES(?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data,episode_id=excluded.episode_id,updated_at=excluded.updated_at",
                        (kind, identity, episode_id, json.dumps(data, ensure_ascii=False, allow_nan=False), iso(now or utcnow())))

    def get(self, kind: str, identity: str) -> dict | None:
        row = self.db.execute("SELECT data FROM records WHERE kind=? AND id=?", (kind, identity)).fetchone()
        return json.loads(row[0]) if row else None

    def records(self, kind: str, episode_id=None) -> list[dict]:
        query, args = "SELECT data FROM records WHERE kind=?", [kind]
        if episode_id:
            query += " AND episode_id=?"
            args.append(episode_id)
        return [json.loads(r[0]) for r in self.db.execute(query + " ORDER BY id", args)]

    def setting(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key: str, value):
        self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))

    def enqueue(self, kind: str, episode_id: str | None, payload: dict, *, key=None, now=None) -> str:
        identity = key or digest({"kind": kind, "episode_id": episode_id, "payload": payload})
        self.db.execute("INSERT OR IGNORE INTO jobs(id,kind,episode_id,payload,status,due_at) VALUES(?,?,?,?,?,?)",
                        (identity, kind, episode_id, json.dumps(payload), "queued", iso(now or utcnow())))
        return identity

    def reserve(self, *, now=None, lease_seconds=900, maximum_attempts=3) -> dict | None:
        now = instant(now or utcnow())
        with self.transaction():
            # Only local compute is eligible for replay. A lost sending process is uncertain.
            self.db.execute("UPDATE publications SET status='unknown',updated_at=? WHERE status='sending' AND id IN (SELECT json_extract(payload,'$.publication_id') FROM jobs WHERE status='running' AND lease_until<=?)", (iso(now), iso(now)))
            self.db.execute("UPDATE jobs SET status=CASE WHEN kind='dispatch' THEN 'unknown' WHEN attempts>=? THEN 'failed' ELSE 'queued' END,owner=NULL,lease_until=NULL WHERE status='running' AND lease_until<=?", (maximum_attempts, iso(now)))
            paused_filter = " AND kind IN ('collect','report')" if self.setting("paused", False) else ""
            row = self.db.execute("SELECT * FROM jobs WHERE status='queued' AND due_at<=? AND attempts<?"+paused_filter+" ORDER BY due_at,id LIMIT 1", (iso(now), maximum_attempts)).fetchone()
            if row is None:
                return None
            owner = str(uuid.uuid4())
            self.db.execute("UPDATE jobs SET status='running',attempts=attempts+1,owner=?,lease_until=? WHERE id=?", (owner, iso(now+timedelta(seconds=lease_seconds)), row["id"]))
            return {**dict(row), "owner": owner, "attempts": row["attempts"]+1, "payload": json.loads(row["payload"])}

    def renew(self, job_id: str, owner: str, *, now=None, seconds=900):
        count = self.db.execute("UPDATE jobs SET lease_until=? WHERE id=? AND owner=? AND status='running'", (iso(instant(now or utcnow())+timedelta(seconds=seconds)), job_id, owner)).rowcount
        if count != 1:
            raise RuntimeError("La réservation du job a été perdue.")

    def finish(self, job: dict, *, status="completed", error=None, due_at=None):
        count = self.db.execute("UPDATE jobs SET status=?,last_error=?,due_at=COALESCE(?,due_at),owner=NULL,lease_until=NULL WHERE id=? AND owner=? AND status='running'",
                               (status, error, iso(due_at) if due_at else None, job["id"], job["owner"])).rowcount
        if count != 1:
            raise RuntimeError("Résultat refusé : réservation du job perdue.")

    def jobs(self) -> list[dict]:
        return [{**dict(r), "payload": json.loads(r["payload"])} for r in self.db.execute("SELECT * FROM jobs ORDER BY due_at,id")]

    def publication(self, identity: str) -> dict | None:
        row = self.db.execute("SELECT * FROM publications WHERE id=?", (identity,)).fetchone()
        return self._publication(row) if row else None

    @staticmethod
    def _publication(row):
        return {**json.loads(row["data"]), **{key: row[key] for key in row.keys() if key != "data"}}

    def publications(self, episode_id=None, platform=None) -> list[dict]:
        query, args = "SELECT * FROM publications WHERE 1=1", []
        for field, value in (("episode_id", episode_id), ("platform", platform)):
            if value:
                query += f" AND {field}=?"
                args.append(value)
        return [self._publication(r) for r in self.db.execute(query+" ORDER BY scheduled_at,id", args)]

    def save_publication(self, value: dict, *, now=None):
        self.db.execute("INSERT INTO publications VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET asset_id=excluded.asset_id,status=excluded.status,scheduled_at=excluded.scheduled_at,remote_id=excluded.remote_id,data=excluded.data,updated_at=excluded.updated_at",
                        (value["id"], value["episode_id"], value["platform"], value["account_id"], value["asset_id"], value["status"], value.get("scheduled_at"), value.get("remote_id"), json.dumps(value, ensure_ascii=False, allow_nan=False), iso(now or utcnow())))

    def retry(self, job_id: str, *, now=None):
        with self.transaction():
            row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row or row["status"] not in {"failed", "blocked"}:
                raise ValueError("Seuls les jobs locaux échoués ou bloqués sont reprenables ; résultat inconnu à réconcilier.")
            if row["kind"] == "dispatch":
                publication = self.publication(json.loads(row["payload"])["publication_id"])
                if publication["status"] in {"unknown", "sending", "published", "simulated", "expired", "cancelled"}:
                    raise ValueError("Cette publication ne permet pas de renvoi.")
                publication["status"] = "scheduled"
                self.save_publication(publication, now=now)
            self.db.execute("UPDATE jobs SET status='queued',attempts=0,last_error=NULL,due_at=? WHERE id=?", (iso(now or utcnow()), job_id))
            self.event("retry_requested", job_id, {}, now=now)

    def backup(self, target: Path):
        target = target.resolve()
        if target.exists() or target == self.path:
            raise ValueError("La sauvegarde exige un nouveau fichier distinct de la base.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(target)) as destination:
            self.db.backup(destination)
        inventory = {"version": 1, "database": target.name, "database_sha256": __import__("hashlib").sha256(target.read_bytes()).hexdigest(),
                     "created_at": iso(utcnow()), "media": [{"path": x["path"], "sha256": x["sha256"]} for x in self.records("asset")]}
        target.with_suffix(".manifest.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        return inventory
