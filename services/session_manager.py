import uuid
from datetime import datetime
from data.db import get_connection


class SessionManager:

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(self, procedure_id: str | None = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = get_connection()
        conn.execute(
            "INSERT INTO sessions (id, created_at, updated_at, procedure_id, status) "
            "VALUES (?,?,?,?,?)",
            (session_id, now, now, procedure_id, "active"),
        )
        conn.commit()
        conn.close()
        return session_id

    def update_session(self, session_id: str, **kwargs):
        now = datetime.now().isoformat()
        fields = ["updated_at=?"]
        values: list = [now]
        for key in ("procedure_id", "status"):
            if key in kwargs and kwargs[key] is not None:
                fields.append(f"{key}=?")
                values.append(kwargs[key])
        values.append(session_id)
        conn = get_connection()
        conn.execute(
            f"UPDATE sessions SET {', '.join(fields)} WHERE id=?",
            values,
        )
        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 10) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT s.id, s.created_at, s.updated_at, s.procedure_id, s.status,
                   COUNT(m.id) AS nb_messages
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def close_session(self, session_id: str):
        self.update_session(session_id, status="closed")

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def save_message(self, session_id: str, role: str, content: str):
        conn = get_connection()
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?,?,?)",
            (session_id, role, content),
        )
        conn.commit()
        conn.close()

    def get_messages(self, session_id: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT role, content, timestamp FROM messages "
            "WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Collected info
    # ------------------------------------------------------------------

    def save_collected_info(
        self, session_id: str, step_id: int, key: str, value: str
    ):
        conn = get_connection()
        conn.execute(
            "INSERT INTO collected_info "
            "(session_id, step_id, field_key, field_value) VALUES (?,?,?,?)",
            (session_id, step_id, key, value),
        )
        conn.commit()
        conn.close()

    def get_collected_info(self, session_id: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT step_id, field_key, field_value, recorded_at "
            "FROM collected_info WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Steps progress
    # ------------------------------------------------------------------

    def upsert_step_progress(
        self, session_id: str, step_id: int, title: str, status: str
    ):
        now = datetime.now().isoformat()
        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM steps_progress WHERE session_id=? AND step_id=?",
            (session_id, step_id),
        ).fetchone()

        if existing:
            if status == "done":
                conn.execute(
                    "UPDATE steps_progress SET status=?, completed_at=? "
                    "WHERE session_id=? AND step_id=?",
                    (status, now, session_id, step_id),
                )
            else:
                conn.execute(
                    "UPDATE steps_progress SET status=? "
                    "WHERE session_id=? AND step_id=?",
                    (status, session_id, step_id),
                )
        else:
            started_at   = now if status == "in_progress" else None
            completed_at = now if status == "done"        else None
            conn.execute(
                "INSERT INTO steps_progress "
                "(session_id, step_id, step_title, status, started_at, completed_at) "
                "VALUES (?,?,?,?,?,?)",
                (session_id, step_id, title, status, started_at, completed_at),
            )
        conn.commit()
        conn.close()

    def get_steps_progress(self, session_id: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT step_id, step_title, status, started_at, completed_at "
            "FROM steps_progress WHERE session_id=? ORDER BY step_id",
            (session_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
