from enum import Enum
from services.kb_loader import KBLoader


class StepStatus(Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    BLOCKED     = "blocked"


class Planner:

    def __init__(self, kb_loader: KBLoader | None = None):
        self.kb_loader: KBLoader = kb_loader or KBLoader()
        self.plan: list[dict]    = []
        self.goal: str           = ""
        self.procedure: dict     = {}

    # ------------------------------------------------------------------
    # Plan creation
    # ------------------------------------------------------------------

    def create_plan(self, procedure_id: str) -> list[dict]:
        self.goal      = procedure_id
        self.procedure = self.kb_loader.load_procedure(procedure_id)
        etapes         = self.procedure.get("etapes", [])
        self.plan      = []
        for i, etape in enumerate(etapes):
            self.plan.append({
                **etape,
                "infos_collectees": {},
                "statut": StepStatus.IN_PROGRESS if i == 0 else StepStatus.PENDING,
            })
        return self.plan

    # ------------------------------------------------------------------
    # Step navigation
    # ------------------------------------------------------------------

    def current_step(self) -> dict | None:
        for step in self.plan:
            if step["statut"] == StepStatus.IN_PROGRESS:
                return step
        return None

    def missing_info(self) -> str | None:
        step = self.current_step()
        if not step:
            return None
        for info in step["infos_requises"]:
            if info not in step["infos_collectees"]:
                return info
        return None

    def missing_info_label(self) -> str | None:
        step = self.current_step()
        if not step:
            return None
        missing = self.missing_info()
        if not missing:
            return None
        labels = step.get("labels_infos", {})
        return labels.get(missing, missing.replace("_", " ").title())

    def record_info(self, key: str, value: str):
        step = self.current_step()
        if not step:
            return
        step["infos_collectees"][key] = value
        if self._is_step_complete(step):
            step["statut"] = StepStatus.DONE
            self._activate_next_step()

    # ------------------------------------------------------------------
    # Progress & completion
    # ------------------------------------------------------------------

    def _is_step_complete(self, step: dict) -> bool:
        return all(
            info in step["infos_collectees"]
            for info in step["infos_requises"]
        )

    def _activate_next_step(self):
        for step in self.plan:
            if step["statut"] == StepStatus.PENDING:
                step["statut"] = StepStatus.IN_PROGRESS
                return

    def progress(self) -> float:
        if not self.plan:
            return 0.0
        done = sum(1 for s in self.plan if s["statut"] == StepStatus.DONE)
        return done / len(self.plan)

    def is_complete(self) -> bool:
        return bool(self.plan) and all(
            s["statut"] == StepStatus.DONE for s in self.plan
        )

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def plan_summary(self) -> str:
        if not self.plan:
            return "Aucun plan en cours."
        proc_title = self.procedure.get("titre", self.goal)
        lines = [f"Procédure : {proc_title}", "Étapes :"]
        icons = {
            StepStatus.IN_PROGRESS: "▶",
            StepStatus.DONE:        "✓",
            StepStatus.PENDING:     "○",
            StepStatus.BLOCKED:     "✗",
        }
        for s in self.plan:
            icon = icons.get(s["statut"], "?")
            lines.append(f"  {icon} {s['id']}. {s['titre']} [{s['organisme']}]")
        return "\n".join(lines)

    def get_current_step_docs(self) -> list[str]:
        step = self.current_step()
        return step.get("docs_requis", []) if step else []

    def get_total_fees(self) -> int:
        return sum(s.get("frais", 0) for s in self.plan)
