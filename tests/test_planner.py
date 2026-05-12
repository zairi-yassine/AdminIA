import pytest
from agent.planner import Planner, StepStatus
from services.kb_loader import KBLoader


# ── KBLoader ───────────────────────────────────────────────────────────

def test_kb_loader_lists_all_five_procedures():
    kb  = KBLoader()
    ids = [p["id"] for p in kb.list_procedures()]
    for expected in ["sarl_au", "cnss", "ompic", "dgi", "rc"]:
        assert expected in ids, f"Procédure '{expected}' manquante dans la KB"


def test_kb_loader_loads_procedure_by_id():
    kb   = KBLoader()
    proc = kb.load_procedure("sarl_au")
    assert proc["id"] == "sarl_au"
    assert "etapes" in proc
    assert len(proc["etapes"]) > 0


def test_kb_loader_raises_on_unknown_id():
    kb = KBLoader()
    with pytest.raises(FileNotFoundError):
        kb.load_procedure("procedure_inconnue")


@pytest.mark.parametrize("message,expected_id", [
    ("je veux créer une sarl au",    "sarl_au"),
    ("immatriculation cnss",         "cnss"),
    ("déposer une marque ompic",     "ompic"),
    ("identifiant fiscal dgi",       "dgi"),
    ("registre de commerce",         "rc"),
    ("bonjour comment ça va",        "unknown"),
])
def test_detect_intent(message, expected_id):
    kb = KBLoader()
    assert kb.detect_intent(message) == expected_id


# ── Planner ────────────────────────────────────────────────────────────

def test_create_plan_sarl_au_has_five_steps():
    planner = Planner()
    plan    = planner.create_plan("sarl_au")
    assert len(plan) == 5


def test_first_step_is_in_progress_others_pending():
    planner = Planner()
    plan    = planner.create_plan("sarl_au")
    assert plan[0]["statut"] == StepStatus.IN_PROGRESS
    assert all(s["statut"] == StepStatus.PENDING for s in plan[1:])


def test_missing_info_returns_first_required_field():
    planner = Planner()
    planner.create_plan("sarl_au")
    assert planner.missing_info() == "nom_complet"


def test_missing_info_label_returns_human_readable():
    planner = Planner()
    planner.create_plan("sarl_au")
    label = planner.missing_info_label()
    assert label is not None
    assert "nom" in label.lower()


def test_record_info_advances_within_step():
    planner = Planner()
    planner.create_plan("sarl_au")
    planner.record_info("nom_complet", "Yassine Zairi")
    assert "nom_complet" in planner.current_step()["infos_collectees"]
    assert planner.missing_info() == "cin"


def test_step_completes_when_all_info_collected():
    planner = Planner()
    planner.create_plan("sarl_au")
    for info in ["nom_complet", "cin", "adresse"]:
        planner.record_info(info, f"val_{info}")
    assert planner.plan[0]["statut"] == StepStatus.DONE
    assert planner.plan[1]["statut"] == StepStatus.IN_PROGRESS


def test_progress_after_first_step():
    planner = Planner()
    planner.create_plan("sarl_au")
    for info in ["nom_complet", "cin", "adresse"]:
        planner.record_info(info, f"val_{info}")
    assert planner.progress() == pytest.approx(1 / 5)


def test_progress_zero_initially():
    planner = Planner()
    planner.create_plan("sarl_au")
    assert planner.progress() == 0.0


def test_is_complete_false_initially():
    planner = Planner()
    planner.create_plan("sarl_au")
    assert planner.is_complete() is False


def test_is_complete_false_without_plan():
    planner = Planner()
    assert planner.is_complete() is False


def test_get_total_fees_sarl_au():
    planner = Planner()
    planner.create_plan("sarl_au")
    assert planner.get_total_fees() > 0


@pytest.mark.parametrize("proc_id", ["sarl_au", "cnss", "ompic", "dgi", "rc"])
def test_all_procedures_create_valid_plan(proc_id):
    planner = Planner()
    plan    = planner.create_plan(proc_id)
    assert len(plan) > 0
    assert planner.missing_info() is not None or planner.current_step() is not None
