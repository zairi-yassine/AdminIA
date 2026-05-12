import pytest
from services.session_manager import SessionManager


# ── Sessions ───────────────────────────────────────────────────────────

def test_create_session_returns_uuid(tmp_db):
    sm = SessionManager()
    sid = sm.create_session()
    assert len(sid) == 36
    assert sid.count("-") == 4


def test_create_session_stored_in_db(tmp_db):
    sm = SessionManager()
    sid = sm.create_session()
    session = sm.get_session(sid)
    assert session is not None
    assert session["id"] == sid
    assert session["status"] == "active"


def test_create_session_with_procedure(tmp_db):
    sm = SessionManager()
    sid = sm.create_session(procedure_id="sarl_au")
    session = sm.get_session(sid)
    assert session["procedure_id"] == "sarl_au"


def test_get_session_unknown_returns_none(tmp_db):
    sm = SessionManager()
    assert sm.get_session("nonexistent-id") is None


def test_update_session_procedure(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.update_session(sid, procedure_id="cnss")
    session = sm.get_session(sid)
    assert session["procedure_id"] == "cnss"


def test_close_session_updates_status(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.close_session(sid)
    session = sm.get_session(sid)
    assert session["status"] == "closed"


def test_list_sessions_returns_most_recent_first(tmp_db):
    sm = SessionManager()
    s1 = sm.create_session(procedure_id="sarl_au")
    s2 = sm.create_session(procedure_id="cnss")
    sessions = sm.list_sessions()
    ids = [s["id"] for s in sessions]
    assert ids.index(s2) < ids.index(s1)


def test_list_sessions_respects_limit(tmp_db):
    sm = SessionManager()
    for _ in range(5):
        sm.create_session()
    sessions = sm.list_sessions(limit=3)
    assert len(sessions) == 3


# ── Messages ───────────────────────────────────────────────────────────

def test_save_and_get_messages(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.save_message(sid, "user",      "Bonjour")
    sm.save_message(sid, "assistant", "Bonjour ! Je suis MAA.")
    msgs = sm.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"]    == "user"
    assert msgs[0]["content"] == "Bonjour"
    assert msgs[1]["role"]    == "assistant"


def test_messages_isolated_between_sessions(tmp_db):
    sm = SessionManager()
    s1 = sm.create_session()
    s2 = sm.create_session()
    sm.save_message(s1, "user", "Message session 1")
    assert sm.get_messages(s2) == []


def test_list_sessions_counts_messages(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.save_message(sid, "user",      "Q1")
    sm.save_message(sid, "assistant", "R1")
    sm.save_message(sid, "user",      "Q2")
    sessions = sm.list_sessions()
    target   = next(s for s in sessions if s["id"] == sid)
    assert target["nb_messages"] == 3


# ── Collected info ─────────────────────────────────────────────────────

def test_save_and_get_collected_info(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.save_collected_info(sid, 1, "nom_complet", "Yassine Zairi")
    sm.save_collected_info(sid, 1, "cin",          "AB123456")
    infos = sm.get_collected_info(sid)
    assert len(infos) == 2
    assert infos[0]["field_key"]   == "nom_complet"
    assert infos[0]["field_value"] == "Yassine Zairi"


# ── Steps progress ─────────────────────────────────────────────────────

def test_upsert_creates_step(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.upsert_step_progress(sid, 1, "Profil du fondateur", "in_progress")
    steps = sm.get_steps_progress(sid)
    assert len(steps) == 1
    assert steps[0]["status"]     == "in_progress"
    assert steps[0]["step_title"] == "Profil du fondateur"


def test_upsert_updates_existing_step(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.upsert_step_progress(sid, 1, "Profil", "in_progress")
    sm.upsert_step_progress(sid, 1, "Profil", "done")
    steps = sm.get_steps_progress(sid)
    assert len(steps) == 1
    assert steps[0]["status"]       == "done"
    assert steps[0]["completed_at"] is not None


def test_upsert_sets_started_at_for_in_progress(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.upsert_step_progress(sid, 1, "Profil", "in_progress")
    steps = sm.get_steps_progress(sid)
    assert steps[0]["started_at"] is not None


def test_steps_ordered_by_step_id(tmp_db):
    sm  = SessionManager()
    sid = sm.create_session()
    sm.upsert_step_progress(sid, 3, "Étape 3", "pending")
    sm.upsert_step_progress(sid, 1, "Étape 1", "done")
    sm.upsert_step_progress(sid, 2, "Étape 2", "in_progress")
    steps = sm.get_steps_progress(sid)
    assert [s["step_id"] for s in steps] == [1, 2, 3]
