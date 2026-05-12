import time

import mlflow

EXPERIMENT_NAME = "maa_agent"
TRACKING_URI    = "sqlite:///data/mlflow.db"


class MLflowTracker:

    def __init__(self, tracking_uri: str = TRACKING_URI):
        self._tracking_uri  = tracking_uri
        self._run_id:  str | None   = None
        self._start:   float | None = None
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(EXPERIMENT_NAME)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(
        self,
        session_id:   str,
        procedure_id: str | None = None,
        lang:         str        = "fr",
        llm_model:    str        = "llama3.2",
    ) -> str:
        run = mlflow.start_run(run_name=f"session_{session_id[:8]}")
        self._run_id = run.info.run_id
        self._start  = time.time()

        mlflow.set_tags({"session_id": session_id, "lang": lang})
        mlflow.log_param("llm_model", llm_model)
        if procedure_id:
            mlflow.log_param("procedure_id", procedure_id)

        return self._run_id

    def end_session(self, completed: bool = False) -> None:
        if not self._run_id:
            return
        elapsed = time.time() - self._start if self._start else 0
        mlflow.log_metric("session_duration_s", round(elapsed, 3))
        mlflow.log_metric("session_completed",  int(completed))
        mlflow.end_run()
        self._run_id = None
        self._start  = None

    # ------------------------------------------------------------------
    # Per-call metrics
    # ------------------------------------------------------------------

    def log_response(
        self,
        response_time_ms: float,
        intent:           str | None = None,
        step:             int        = 0,
    ) -> None:
        if not self._run_id:
            return
        mlflow.log_metric("response_time_ms", round(response_time_ms, 2), step=step)
        if intent:
            mlflow.log_metric(
                "intent_detected", 1 if intent != "unknown" else 0, step=step
            )

    def log_progress(
        self,
        progress:    float,
        steps_done:  int,
        steps_total: int,
        step:        int = 0,
    ) -> None:
        if not self._run_id:
            return
        mlflow.log_metric("progress",    round(progress, 4), step=step)
        mlflow.log_metric("steps_done",  steps_done,         step=step)
        mlflow.log_metric("steps_total", steps_total,        step=step)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        return self._run_id is not None

    def run_id(self) -> str | None:
        return self._run_id
