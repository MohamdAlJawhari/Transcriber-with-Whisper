import sqlite3
from flask import current_app


def get_connection():
    """Create a new database connection."""
    conn = sqlite3.connect(current_app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db(app) -> None:
    """Create the notes table if it doesn't exist."""
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            audio_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    _ensure_audio_column(conn)
    conn.commit()
    conn.close()


def _ensure_audio_column(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(notes);")
    columns = [row[1] for row in cursor.fetchall()]
    if "audio_path" not in columns:
        conn.execute("ALTER TABLE notes ADD COLUMN audio_path TEXT;")
