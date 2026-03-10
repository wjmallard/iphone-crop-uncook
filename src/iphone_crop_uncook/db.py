import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import config

DB_PATH = config.OUTPUT_DIR / config.DB_NAME


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS processed_photos (
            uuid TEXT PRIMARY KEY,
            original_filename TEXT NOT NULL,
            exported_path TEXT NOT NULL,
            is_edited INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sync_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)


def processed_uuids(conn) -> set[str]:
    rows = conn.execute("SELECT uuid FROM processed_photos").fetchall()
    return {r[0] for r in rows}


def mark_processed(conn, uuid, original_filename, exported_path, is_edited):
    conn.execute(
        """INSERT OR REPLACE INTO processed_photos
           (uuid, original_filename, exported_path, is_edited, processed_at)
           VALUES (?, ?, ?, ?, ?)""",
        (uuid, original_filename, exported_path, is_edited,
         datetime.now(timezone.utc).isoformat()),
    )


def get_last_sync(conn) -> datetime | None:
    row = conn.execute(
        "SELECT value FROM sync_state WHERE key = 'last_sync'"
    ).fetchone()
    if row:
        return datetime.fromisoformat(row[0])
    return None


def set_last_sync(conn, dt: datetime):
    conn.execute(
        "INSERT OR REPLACE INTO sync_state (key, value) VALUES ('last_sync', ?)",
        (dt.isoformat(),),
    )
