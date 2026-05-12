import pytest
from agent.planner import StepStatus
from tools.doc_gen import PDFGenerator


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_procedure():
    return {
        "titre":    "Creation SARL a Associe Unique",
        "organisme": ["OMPIC", "Notaire", "Tribunal de Commerce"],
        "duree_est": "2 a 4 semaines",
        "frais_est": {"min": 3000, "max": 5000},
    }


@pytest.fixture
def sample_plan():
    return [
        {
            "id": 1, "titre": "Profil du fondateur",
            "organisme": "—",
            "statut": StepStatus.DONE,
            "frais": 0, "delai": "0 jours",
            "docs_requis": ["CIN", "Justificatif de domicile"],
        },
        {
            "id": 2, "titre": "Capital et siege social",
            "organisme": "—",
            "statut": StepStatus.DONE,
            "frais": 0, "delai": "0 jours",
            "docs_requis": [],
        },
        {
            "id": 3, "titre": "Certificat Negatif OMPIC",
            "organisme": "OMPIC",
            "statut": StepStatus.IN_PROGRESS,
            "frais": 170, "delai": "2 jours",
            "docs_requis": ["CIN", "170 MAD"],
        },
        {
            "id": 4, "titre": "Statuts notaries + depot capital",
            "organisme": "Notaire",
            "statut": StepStatus.PENDING,
            "frais": 2000, "delai": "5 jours",
            "docs_requis": ["Certificat Negatif", "CIN"],
        },
        {
            "id": 5, "titre": "Immatriculation RC + DGI + CNSS",
            "organisme": "Tribunal / DGI / CNSS",
            "statut": StepStatus.PENDING,
            "frais": 350, "delai": "7 jours",
            "docs_requis": ["Statuts", "Certificat Negatif"],
        },
    ]


@pytest.fixture
def sample_info():
    return {
        "nom_complet":  "Yassine Zairi",
        "cin":          "AB123456",
        "adresse":      "Casablanca, Maroc",
        "capital":      "10000",
        "denomination": "Tech Solutions SARL AU",
    }


# ── generate_summary ───────────────────────────────────────────────────

def test_returns_bytes(sample_procedure, sample_plan, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, sample_info, sample_plan)
    assert isinstance(result, bytes)


def test_valid_pdf_header(sample_procedure, sample_plan, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, sample_info, sample_plan)
    assert result[:4] == b"%PDF"


def test_non_empty_output(sample_procedure, sample_plan, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, sample_info, sample_plan)
    assert len(result) > 1000


def test_accepts_empty_collected_info(sample_procedure, sample_plan):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, {}, sample_plan)
    assert isinstance(result, bytes)
    assert result[:4] == b"%PDF"


def test_accepts_empty_plan(sample_procedure, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, sample_info, [])
    assert isinstance(result, bytes)


def test_accepts_empty_session_id(sample_procedure, sample_plan, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(sample_procedure, sample_info, sample_plan, session_id="")
    assert isinstance(result, bytes)


def test_accepts_session_id(sample_procedure, sample_plan, sample_info):
    gen    = PDFGenerator()
    result = gen.generate_summary(
        sample_procedure, sample_info, sample_plan,
        session_id="a3f8c21b-1234-5678-abcd-000000000000"
    )
    assert isinstance(result, bytes)


def test_all_step_statuses_handled(sample_procedure, sample_info):
    gen  = PDFGenerator()
    plan = [
        {"id": i, "titre": f"Etape {i}", "organisme": "Test",
         "statut": s, "frais": 0, "delai": "—", "docs_requis": []}
        for i, s in enumerate(StepStatus, start=1)
    ]
    result = gen.generate_summary(sample_procedure, sample_info, plan)
    assert result[:4] == b"%PDF"


def test_generates_larger_pdf_with_more_info(sample_procedure, sample_plan):
    gen       = PDFGenerator()
    small_pdf = gen.generate_summary(sample_procedure, {}, sample_plan)
    large_pdf = gen.generate_summary(
        sample_procedure,
        {f"field_{i}": f"value_{i}" for i in range(10)},
        sample_plan,
    )
    assert len(large_pdf) > len(small_pdf)
