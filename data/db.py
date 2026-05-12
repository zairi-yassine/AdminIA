import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sessions.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           TEXT PRIMARY KEY,
            created_at   DATETIME NOT NULL,
            updated_at   DATETIME NOT NULL,
            procedure_id TEXT,
            status       TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL REFERENCES sessions(id),
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collected_info (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL REFERENCES sessions(id),
            step_id     INTEGER NOT NULL,
            field_key   TEXT    NOT NULL,
            field_value TEXT    NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS steps_progress (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT    NOT NULL REFERENCES sessions(id),
            step_id      INTEGER NOT NULL,
            step_title   TEXT    NOT NULL,
            status       TEXT    DEFAULT 'pending',
            started_at   DATETIME,
            completed_at DATETIME
        );
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Base de données initialisée : {DB_PATH}")
