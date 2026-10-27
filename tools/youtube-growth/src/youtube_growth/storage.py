from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextmanager
def exclusive_run(directory: Path):
    """A stale lock is deliberately not removed automatically after a crash."""
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "run.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise RuntimeError(f"Traitement déjà actif ou interrompu. Vérifiez {lock} avant de retirer ce verrou.") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


class Journal:
    """Write intent before network effects; never replay an ambiguous write."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, result TEXT, updated_at TEXT NOT NULL)")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def begin(self, kind: str, payload: dict, identity: dict | None = None) -> tuple[str, bool]:
        operation_id = digest({"kind": kind, "payload": identity if identity is not None else payload})
        with self.connection:
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO operations VALUES (?, ?, ?, 'started', NULL, ?)",
                (operation_id, kind, json.dumps(payload, ensure_ascii=False), now_iso()),
            )
        if cursor.rowcount == 1:
            return operation_id, True
        row = self.connection.execute("SELECT status FROM operations WHERE id = ?", (operation_id,)).fetchone()
        if row["status"] != "complete":
            raise RuntimeError(f"Opération {operation_id[:12]} incertaine. Vérifier YouTube avant toute reprise.")
        return operation_id, False

    def finish(self, operation_id: str, result: dict) -> None:
        with self.connection:
            self.connection.execute("UPDATE operations SET status='complete', result=?, updated_at=? WHERE id=?", (json.dumps(result, ensure_ascii=False), now_iso(), operation_id))

    def entries(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute("SELECT id,kind,status,updated_at FROM operations ORDER BY updated_at DESC")]

    def result(self, operation_id: str) -> dict | None:
        row = self.connection.execute("SELECT result FROM operations WHERE id=? AND status='complete'", (operation_id,)).fetchone()
        return json.loads(row['result']) if row and row['result'] else None


def remote_journal_configured() -> bool:
    return bool(os.environ.get("YOUTUBE_JOURNAL_DATABASE_URL", "").strip())


def open_journal(path: Path):
    url = os.environ.get("YOUTUBE_JOURNAL_DATABASE_URL", "").strip()
    if url:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or "-pooler" in parsed.hostname:
            raise RuntimeError("Le journal exige une URL Postgres directe, sans pool de transactions.")
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} and parse_qs(parsed.query).get("sslmode", [""])[0] not in {"require", "verify-ca", "verify-full"}:
            raise RuntimeError("Le journal distant exige sslmode=require ou verify-full.")
        from .postgres_storage import PostgresJournal
        return PostgresJournal(url)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise RuntimeError("YOUTUBE_JOURNAL_DATABASE_URL requis pour les écritures depuis GitHub Actions.")
    return Journal(path)


def execute_once(journal, kind: str, identity: dict, payload: dict, action) -> bool:
    operation_id, should_execute = journal.begin(kind, payload, identity=identity)
    if not should_execute:
        return False
    result = action()
    journal.finish(operation_id, {"id": result})
    return True
