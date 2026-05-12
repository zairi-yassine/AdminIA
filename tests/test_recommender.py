import pytest
from services.recommender import Recommender, LEGAL_STATUS_INFO


# ── Profile collection ─────────────────────────────────────────────────

def test_first_question_is_nb_associes():
    rec = Recommender()
    key, label = rec.get_next_question()
    assert key == "nb_associes"
    assert "fondateur" in label.lower() or "personnes" in label.lower()


def test_get_next_question_advances_after_record():
    rec = Recommender()
    rec.record("nb_associes", "1")
    key, _ = rec.get_next_question()
    assert key == "ca_previsionnel"


def test_profile_incomplete_with_three_answers():
    rec = Recommender()
    for key, val in [("nb_associes", "1"), ("ca_previsionnel", "200000"), ("type_activite", "service")]:
        rec.record(key, val)
    assert rec.is_profile_complete() is False


def test_profile_complete_after_four_answers():
    rec = Recommender()
    for key, val in [
        ("nb_associes",      "1"),
        ("ca_previsionnel",  "200000"),
        ("type_activite",    "service"),
        ("capital_disponible", "5000"),
    ]:
        rec.record(key, val)
    assert rec.is_profile_complete() is True


def test_get_next_question_returns_none_when_complete():
    rec = Recommender()
    for key, val in [
        ("nb_associes", "1"), ("ca_previsionnel", "200000"),
        ("type_activite", "service"), ("capital_disponible", "5000"),
    ]:
        rec.record(key, val)
    assert rec.get_next_question() is None


# ── Decision tree ──────────────────────────────────────────────────────

def _make_recommender(nb, ca, activite, capital) -> Recommender:
    rec = Recommender()
    rec.record("nb_associes",       str(nb))
    rec.record("ca_previsionnel",   str(ca))
    rec.record("type_activite",     activite)
    rec.record("capital_disponible", str(capital))
    return rec


def test_solo_service_small_ca_recommends_auto_entrepreneur():
    rec = _make_recommender(1, 200_000, "service", 5_000)
    result = rec.analyze()
    assert result["status_id"] == "auto_entrepreneur"


def test_solo_artisan_small_ca_recommends_auto_entrepreneur():
    rec = _make_recommender(1, 300_000, "artisanat", 10_000)
    result = rec.analyze()
    assert result["status_id"] == "auto_entrepreneur"


def test_solo_large_ca_recommends_sarl_au():
    rec = _make_recommender(1, 800_000, "service", 50_000)
    result = rec.analyze()
    assert result["status_id"] == "sarl_au"


def test_solo_commerce_recommends_sarl_au():
    rec = _make_recommender(1, 200_000, "commerce", 10_000)
    result = rec.analyze()
    assert result["status_id"] == "sarl_au"


def test_two_associates_recommends_sarl():
    rec = _make_recommender(2, 500_000, "service", 20_000)
    result = rec.analyze()
    assert result["status_id"] == "sarl"


def test_five_associates_large_capital_recommends_sa():
    rec = _make_recommender(5, 2_000_000, "industrie", 300_000)
    result = rec.analyze()
    assert result["status_id"] == "sa"


def test_three_associates_recommends_sarl():
    rec = _make_recommender(3, 600_000, "commerce", 50_000)
    result = rec.analyze()
    assert result["status_id"] == "sarl"


# ── Procedure mapping ──────────────────────────────────────────────────

def test_sarl_au_has_procedure_in_maa():
    rec = _make_recommender(1, 800_000, "service", 50_000)
    result = rec.analyze()
    assert result["procedure_id"] == "sarl_au"


def test_auto_entrepreneur_has_no_procedure_yet():
    rec = _make_recommender(1, 200_000, "service", 5_000)
    result = rec.analyze()
    assert result["procedure_id"] is None


def test_sarl_has_no_procedure_yet():
    rec = _make_recommender(2, 500_000, "service", 20_000)
    result = rec.analyze()
    assert result["procedure_id"] is None


# ── Format output ──────────────────────────────────────────────────────

def test_format_recommendation_contains_status_name():
    rec = _make_recommender(1, 800_000, "service", 50_000)
    rec.analyze()
    text = rec.format_recommendation()
    assert "SARL" in text


def test_format_recommendation_contains_avantages():
    rec = _make_recommender(1, 800_000, "service", 50_000)
    rec.analyze()
    text = rec.format_recommendation()
    assert "Avantages" in text or "avantages" in text.lower()


def test_format_recommendation_cta_if_procedure_exists():
    rec = _make_recommender(1, 800_000, "service", 50_000)
    rec.analyze()
    text = rec.format_recommendation()
    assert "MAA" in text


# ── Legal status info completeness ────────────────────────────────────

@pytest.mark.parametrize("status_id", ["auto_entrepreneur", "sarl_au", "sarl", "sa"])
def test_all_statuses_have_required_fields(status_id):
    info = LEGAL_STATUS_INFO[status_id]
    for field in ["nom", "description", "avantages", "inconvenients", "ideal_pour"]:
        assert field in info, f"Champ '{field}' manquant pour '{status_id}'"


# ── Reset ─────────────────────────────────────────────────────────────

def test_reset_clears_collected_info():
    rec = _make_recommender(1, 200_000, "service", 5_000)
    rec.analyze()
    rec.reset()
    assert rec.collected == {}
    assert rec.result is None
