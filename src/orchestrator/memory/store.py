from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock


class PersistentMemoryStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_memory (
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY(session_id, agent_name, key)
                )
                """
            )
            conn.commit()

    def upsert(self, session_id: str, agent_name: str, key: str, value: str) -> None:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO agent_memory(session_id, agent_name, key, value)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(session_id, agent_name, key)
                    DO UPDATE SET value=excluded.value
                    """,
                    (session_id, agent_name, key, value),
                )
                conn.commit()

    def get(self, session_id: str, agent_name: str, key: str) -> str | None:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT value FROM agent_memory WHERE session_id=? AND agent_name=? AND key=?",
                (session_id, agent_name, key),
            ).fetchone()
        return row[0] if row else None
