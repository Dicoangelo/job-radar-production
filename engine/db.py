"""SQLite connection helper. Resolves DB path and ensures schema is loaded."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DATA_DIR = Path.home() / ".job-radar"
DB_PATH = DATA_DIR / "radar.db"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def init_db() -> Path:
    """Create ~/.job-radar/ and apply schema if DB is new."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    is_new = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    if is_new:
        conn.executescript(SCHEMA.read_text())
        conn.commit()
        print(f"initialized DB at {DB_PATH}", file=sys.stderr)
    conn.close()
    return DB_PATH


def connect() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


if __name__ == "__main__":
    init_db()
    print(f"DB at {DB_PATH}")
