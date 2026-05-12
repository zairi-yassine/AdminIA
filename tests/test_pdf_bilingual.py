import pytest
from agent.planner import StepStatus
from tools.pdf_bilingual import BilingualPDFGenerator


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def procedure():
    return {
        "id":        "sarl_au",
        "titre":     "Creation SARL a Associe Unique",
        "organisme": ["OMPIC", "Notaire", "Tribunal de Commerce"],
        "duree_est": "2 a 4 semaines",
        "frais_est": {"min": 3000, "max": 5000},
    }


@pytest.fixture
def plan():
    return [
        {"id": 1, "titre": "Profil du fondateur",   "organisme": "-",
         "statut": StepStatus.DONE,        "frais": 0,    "delai": "0 jours",
         "docs_requis": ["CIN"]},
        {"id": 2, "titre": "Capital social",         "organisme": "-",
         "statut": StepStatus.IN_PROGRESS, "frais": 0,    "delai": "0 jours",
         "docs_requis": []},
        {"id": 3, "titre": "Certificat Negatif",     "organisme": "OMPIC",
         "statut": StepStatus.PENDING,     "frais": 170,  "delai": "2 jours",
         "docs_requis": ["CIN", "170 MAD"]},
    ]


@pytest.fixture
def info():
    return {"nom_complet": "Yassine Zairi", "cin": "AB123456", "capital": "10000"}


# ── generate_bilingual ─────────────────────────────────────────────────

def test_returns_bytes(procedure, plan, info):
    result = BilingualPDFGenerator().generate_bilingual(procedure, info, plan)
    assert isinstance(result, bytes)


def test_valid_pdf_header(procedure, plan, info):
    result = BilingualPDFGenerator().generate_bilingual(procedure, info, plan)
    assert result[:4] == b"%PDF"


def test_larger_than_french_only(procedure, plan, info):
    from tools.doc_gen import PDFGenerator
    fr_only  = PDFGenerator().generate_summary(procedure, info, plan)
    bilingual = BilingualPDFGenerator().generate_bilingual(procedure, info, plan)
    assert len(bilingual) > len(fr_only)


def test_accepts_empty_info(procedure, plan):
    result = BilingualPDFGenerator().generate_bilingual(procedure, {}, plan)
    assert result[:4] == b"%PDF"


def test_accepts_empty_plan(procedure, info):
    result = BilingualPDFGenerator().generate_bilingual(procedure, info, [])
    assert result[:4] == b"%PDF"


def test_accepts_session_id(procedure, plan, info):
    result = BilingualPDFGenerator().generate_bilingual(
        procedure, info, plan, session_id="a1b2c3d4-1234-5678-abcd-000000000000"
    )
    assert isinstance(result, bytes)


def test_all_procedure_ids_work(plan, info):
    gen = BilingualPDFGenerator()
    for pid in ["sarl_au", "cnss", "ompic", "dgi", "rc"]:
        proc = {"id": pid, "titre": f"Proc {pid}", "organisme": [],
                "duree_est": "-", "frais_est": {"min": 0, "max": 0}}
        result = gen.generate_bilingual(proc, info, plan)
        assert result[:4] == b"%PDF", f"Échec pour {pid}"


def test_all_step_statuses_arabic(procedure, info):
    gen  = BilingualPDFGenerator()
    plan = [
        {"id": i, "titre": f"Etape {i}", "organisme": "-",
         "statut": s, "frais": 0, "delai": "-", "docs_requis": []}
        for i, s in enumerate(StepStatus, start=1)
    ]
    result = gen.generate_bilingual(procedure, info, plan)
    assert result[:4] == b"%PDF"
