import mlflow
import pytest
from services.mlflow_tracker import EXPERIMENT_NAME, MLflowTracker


@pytest.fixture
def tracker(tmp_path):
    uri = f"sqlite:///{tmp_path}/test_mlflow.db"
    return MLflowTracker(tracking_uri=uri)


@pytest.fixture
def active(tracker):
    tracker.start_session("aaaa-bbbb-cccc-dddd")
    yield tracker
    if tracker.is_active():
        tracker.end_session()


# ── État initial ─────────────────────────────────────────────────────

def test_not_active_initially(tracker):
    assert not tracker.is_active()


def test_run_id_none_initially(tracker):
    assert tracker.run_id() is None


def test_experiment_name_constant():
    assert EXPERIMENT_NAME == "maa_agent"


# ── start_session ─────────────────────────────────────────────────────

def test_start_session_returns_run_id(tracker):
    rid = tracker.start_session("test-session-id-1234")
    assert isinstance(rid, str) and len(rid) > 0
    tracker.end_session()


def test_is_active_after_start(tracker):
    tracker.start_session("test-session-id-0001")
    assert tracker.is_active()
    tracker.end_session()


def test_run_id_set_after_start(tracker):
    rid = tracker.start_session("test-session-id-0002")
    assert tracker.run_id() == rid
    tracker.end_session()


def test_start_session_with_procedure_id(tracker):
    rid = tracker.start_session("test-0003", procedure_id="sarl_au")
    assert rid is not None
    tracker.end_session()


def test_start_session_with_lang(tracker):
    rid = tracker.start_session("test-0004", lang="ar")
    assert rid is not None
    tracker.end_session()


def test_start_session_with_llm_model(tracker):
    rid = tracker.start_session("test-0005", llm_model="mistral:7b")
    assert rid is not None
    tracker.end_session()


# ── end_session ───────────────────────────────────────────────────────

def test_is_not_active_after_end(tracker):
    tracker.start_session("test-end-0001")
    tracker.end_session()
    assert not tracker.is_active()


def test_run_id_none_after_end(tracker):
    tracker.start_session("test-end-0002")
    tracker.end_session()
    assert tracker.run_id() is None


def test_end_session_completed_true(tracker):
    tracker.start_session("test-end-0003")
    tracker.end_session(completed=True)
    assert not tracker.is_active()


def test_end_session_completed_false(tracker):
    tracker.start_session("test-end-0004")
    tracker.end_session(completed=False)
    assert not tracker.is_active()


def test_end_session_without_active_run_no_error(tracker):
    tracker.end_session()
    assert not tracker.is_active()


# ── log_response ──────────────────────────────────────────────────────

def test_log_response_no_error(active):
    active.log_response(response_time_ms=350.5, intent="sarl_au", step=1)


def test_log_response_without_active_run_no_error(tracker):
    tracker.log_response(response_time_ms=100.0)


def test_log_response_unknown_intent(active):
    active.log_response(response_time_ms=200.0, intent="unknown", step=1)


# ── log_progress ──────────────────────────────────────────────────────

def test_log_progress_no_error(active):
    active.log_progress(progress=0.5, steps_done=2, steps_total=4, step=1)


def test_log_progress_without_active_run_no_error(tracker):
    tracker.log_progress(progress=0.0, steps_done=0, steps_total=5)


def test_log_progress_complete(active):
    active.log_progress(progress=1.0, steps_done=5, steps_total=5, step=5)


# ── Replay : start → end → start again ────────────────────────────────

def test_can_start_new_session_after_end(tracker):
    r1 = tracker.start_session("session-A")
    tracker.end_session()
    r2 = tracker.start_session("session-B")
    assert r1 != r2
    tracker.end_session()
