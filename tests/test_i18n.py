import pytest
from services.i18n import (
    PROCEDURE_TITLES_AR,
    STEP_STATUS_AR,
    SUPPORTED_LANGS,
    TRANSLATIONS,
    t,
)


# ── Structure des traductions ──────────────────────────────────────────

def test_both_languages_present():
    assert "fr" in TRANSLATIONS
    assert "ar" in TRANSLATIONS


def test_all_fr_keys_exist_in_ar():
    missing = set(TRANSLATIONS["fr"]) - set(TRANSLATIONS["ar"])
    assert not missing, f"Clés manquantes en arabe : {missing}"


def test_all_ar_keys_exist_in_fr():
    missing = set(TRANSLATIONS["ar"]) - set(TRANSLATIONS["fr"])
    assert not missing, f"Clés manquantes en français : {missing}"


def test_no_empty_values_fr():
    for key, val in TRANSLATIONS["fr"].items():
        assert val.strip(), f"Valeur vide pour clé FR : {key}"


def test_no_empty_values_ar():
    for key, val in TRANSLATIONS["ar"].items():
        assert val.strip(), f"Valeur vide pour clé AR : {key}"


# ── Fonction t() ─────────────────────────────────────────────────────

def test_t_returns_french_by_default():
    result = t("app_title")
    assert "MAA" in result
    assert "Morocco" in result


def test_t_returns_french_explicit():
    assert t("step_done", "fr") == "Complété"


def test_t_returns_arabic():
    assert t("step_done", "ar") == "مكتمل"


def test_t_unknown_lang_falls_back_to_fr():
    assert t("step_done", "zh") == t("step_done", "fr")


def test_t_unknown_key_returns_key():
    assert t("nonexistent_key_xyz", "fr") == "nonexistent_key_xyz"


def test_t_unknown_key_ar_falls_back_to_key():
    assert t("nonexistent_key_xyz", "ar") == "nonexistent_key_xyz"


# ── Clés critiques ────────────────────────────────────────────────────

@pytest.mark.parametrize("key", [
    "app_title", "app_caption",
    "sidebar_progress", "sidebar_new",
    "chat_placeholder",
    "completion_msg", "pdf_download",
    "step_done", "step_pending",
    "pdf_section_meta", "pdf_section_plan",
])
def test_critical_key_present_both_langs(key):
    assert t(key, "fr")
    assert t(key, "ar")


# ── PROCEDURE_TITLES_AR ───────────────────────────────────────────────

def test_procedure_titles_ar_has_all_5():
    expected = {"sarl_au", "cnss", "ompic", "dgi", "rc"}
    assert expected == set(PROCEDURE_TITLES_AR.keys())


def test_procedure_titles_ar_non_empty():
    for pid, title in PROCEDURE_TITLES_AR.items():
        assert title.strip(), f"Titre arabe vide pour {pid}"


# ── STEP_STATUS_AR ────────────────────────────────────────────────────

def test_step_status_ar_has_all_4():
    expected = {"done", "in_progress", "pending", "blocked"}
    assert expected == set(STEP_STATUS_AR.keys())


def test_step_status_ar_non_empty():
    for status, label in STEP_STATUS_AR.items():
        assert label.strip(), f"Label arabe vide pour statut {status}"


# ── SUPPORTED_LANGS ───────────────────────────────────────────────────

def test_supported_langs_contains_fr_ar():
    assert "fr" in SUPPORTED_LANGS
    assert "ar" in SUPPORTED_LANGS
