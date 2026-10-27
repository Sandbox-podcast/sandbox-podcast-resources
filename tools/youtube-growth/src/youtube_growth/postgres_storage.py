from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import asdict

from .core import State
from .identity import expected_channel_id
from .storage import digest


class PostgresJournal:
    """Committed intents survive runners; an ambiguous attempt is never replayed."""

    def __init__(self, url: str):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as error:
            raise RuntimeError("Installez requirements.txt pour utiliser le journal Postgres.") from error
        try:
            self.connection = psycopg.connect(url, autocommit=True, row_factory=dict_row,
                                             connect_timeout=10, options="-c statement_timeout=15000")
            # No implicit migrations and no fallback to a disposable SQLite file.
            self.connection.execute("SELECT id FROM youtube_operations LIMIT 0")
            self.connection.execute("SELECT channel_id FROM youtube_poll_state LIMIT 0")
        except psycopg.Error:
            if hasattr(self, "connection"):
                self.connection.close()
            raise RuntimeError("Journal Postgres indisponible. Vérifiez la cible, les droits et la migration.") from None

    def close(self) -> None:
        self.connection.close()

    def begin(self, kind: str, payload: dict, identity: dict | None = None) -> tuple[str, bool]:
        operation_id = digest({"kind": kind, "payload": identity if identity is not None else payload})
        row = self.connection.execute(
            "INSERT INTO youtube_operations (id,kind,payload,status) VALUES (%s,%s,%s::jsonb,'started') "
            "ON CONFLICT (id) DO NOTHING RETURNING id",
            (operation_id, kind, json.dumps(payload, ensure_ascii=False, allow_nan=False)),
        ).fetchone()
        if row:
            return operation_id, True
        previous = self.connection.execute("SELECT status FROM youtube_operations WHERE id=%s", (operation_id,)).fetchone()
        if not previous or previous["status"] != "complete":
            raise RuntimeError(f"Opération {operation_id[:12]} incertaine. Vérifier YouTube avant toute reprise.")
        return operation_id, False

    def finish(self, operation_id: str, result: dict) -> None:
        self.connection.execute(
            "UPDATE youtube_operations SET status='complete',result=%s::jsonb,updated_at=now() WHERE id=%s",
            (json.dumps(result, ensure_ascii=False, allow_nan=False), operation_id),
        )

    def entries(self) -> list[dict]:
        return [dict(row, updated_at=row["updated_at"].isoformat()) for row in
                self.connection.execute("SELECT id,kind,status,updated_at FROM youtube_operations ORDER BY updated_at DESC")]

    def result(self, operation_id: str) -> dict | None:
        row = self.connection.execute("SELECT result FROM youtube_operations WHERE id=%s AND status='complete'", (operation_id,)).fetchone()
        return row['result'] if row else None

    def load_state(self) -> State:
        row = self.connection.execute("SELECT payload FROM youtube_poll_state WHERE channel_id=%s", (expected_channel_id(),)).fetchone()
        return State.from_dict(row["payload"]) if row else State()

    def save_state(self, state: State) -> None:
        self.connection.execute(
            "INSERT INTO youtube_poll_state (channel_id,payload) VALUES (%s,%s::jsonb) "
            "ON CONFLICT (channel_id) DO UPDATE SET payload=EXCLUDED.payload,updated_at=now()",
            (expected_channel_id(), json.dumps(asdict(state), allow_nan=False)),
        )

    @contextmanager
    def exclusive_poll(self):
        # Requires an unpooled connection: this lock belongs to the database session.
        lock_id = int(digest({"channel": expected_channel_id(), "job": "poll"})[:15], 16)
        locked = self.connection.execute("SELECT pg_try_advisory_lock(%s) AS locked", (lock_id,)).fetchone()
        if not locked or not locked["locked"]:
            raise RuntimeError("Un polling YouTube est déjà actif pour cette chaîne.")
        try:
            yield
        finally:
            self.connection.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))
