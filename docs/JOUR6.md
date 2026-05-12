# Documentation Jour 6 — Bilingue Arabe/Français (App v0.6)

> **Date** : 12 Mai 2026  
> **Livrable** : Interface bilingue FR/AR + PDF deux pages + RTL Streamlit

---

## 1. Ce qui a été ajouté

### Fichiers créés

| Fichier | Description |
|---|---|
| `services/i18n.py` | Système de traductions FR/AR |
| `tools/pdf_bilingual.py` | `BilingualPDFGenerator` — PDF 2 pages |
| `tests/test_i18n.py` | 27 tests i18n |
| `tests/test_pdf_bilingual.py` | 8 tests PDF bilingue |

### Fichiers modifiés

| Fichier | Changement |
|---|---|
| `app.py` | Sélecteur langue + CSS RTL + labels i18n + BilingualPDFGenerator |
| `pyproject.toml` | +`arabic-reshaper>=3.0.0`, `python-bidi>=0.4.2` |
| `requirements.txt` | idem |

---

## 2. `services/i18n.py` — Système de traductions

### Structure

```python
TRANSLATIONS = {
    "fr": { "app_title": "MAA — Morocco Administrative Agent", ... },
    "ar": { "app_title": "MAA — وكيل إداري مغربي", ... },
}

PROCEDURE_TITLES_AR = {
    "sarl_au": "إنشاء شركة ذات مسؤولية محدودة بشريك وحيد",
    "cnss":    "التسجيل في الصندوق الوطني للضمان الاجتماعي",
    "ompic":   "تسجيل علامة تجارية لدى OMPIC",
    "dgi":     "الحصول على المعرف الضريبي",
    "rc":      "التسجيل في السجل التجاري",
}

STEP_STATUS_AR = {
    "done":        "مكتمل",
    "in_progress": "جارٍ",
    "pending":     "في الانتظار",
    "blocked":     "محظور",
}

def t(key: str, lang: str = "fr") -> str:
    ...  # fallback: lang inconnu → fr, clé inconnue → clé elle-même
```

### Clés couvertes (30 clés × 2 langues = 60 traductions)

- App : `app_title`, `app_caption`
- Sidebar : `sidebar_progress`, `sidebar_collected`, `sidebar_session`, `sidebar_recent`, `sidebar_procedures`, `sidebar_new`, `sidebar_lang`
- Chat : `chat_placeholder`, `chat_thinking`
- Complétion : `completion_msg`, `pdf_download`, `pdf_unavailable`
- Statuts : `step_done`, `step_in_progress`, `step_pending`, `step_blocked`
- PDF : `pdf_header_sub`, `pdf_generated`, `pdf_section_meta`, `pdf_section_info`, `pdf_section_plan`, `pdf_orgs`, `pdf_duration`, `pdf_fees_est`, `pdf_fees_calc`, `pdf_footer`

---

## 3. `tools/pdf_bilingual.py` — BilingualPDFGenerator

### Pipeline Arabic

```
texte arabe brut
    ↓
arabic_reshaper.reshape()   # jonction des glyphes (ligatures)
    ↓
bidi.algorithm.get_display() # ordre RTL pour affichage
    ↓
fpdf.cell(align="R")         # alignement droite dans le PDF
```

### Police utilisée

```
C:/Windows/Fonts/arial.ttf   # Windows (disponible sur machine étudiant)
/usr/share/fonts/.../DejaVuSans.ttf  # Linux fallback
/System/Library/Fonts/Arial.ttf     # macOS fallback
```

Arial supporte les glyphes arabes. Combiné avec `arabic_reshaper` + `python-bidi`, le rendu est correct pour les documents administratifs.

### Structure du PDF bilingue

```
Page 1 — Français (héritée de PDFGenerator)
┌────────────────────────────────────────────────┐
│  MAA — Morocco Administrative Agent  (vert)    │
│  Résumé de procédure administrative            │
│  Création SARL à Associé Unique                │
├────────────────────────────────────────────────┤
│  INFORMATIONS GÉNÉRALES                        │
│  INFORMATIONS COLLECTÉES                       │
│  PLAN DES ÉTAPES                               │
└────────────────────────────────────────────────┘

Page 2 — Arabe (BilingualPDFGenerator)
┌────────────────────────────────────────────────┐
│  وكيل إداري مغربي — MAA  (vert, RTL)          │
│  ملخص الإجراء الإداري                          │
│  إنشاء شركة ذات مسؤولية محدودة بشريك وحيد     │
├────────────────────────────────────────────────┤
│  معلومات عامة                    (aligné droite)│
│  المعلومات المجمعة                              │
│  خطوات الإجراء                                 │
└────────────────────────────────────────────────┘
```

### API

```python
class BilingualPDFGenerator(PDFGenerator):
    def generate_bilingual(
        procedure, collected_info, plan, session_id=""
    ) -> bytes   # 2 pages : Page 1 FR + Page 2 AR
```

---

## 4. Améliorations `app.py` (v0.6)

### Sélecteur de langue

```python
lang_choice = st.selectbox(
    t("sidebar_lang", lang),
    options=["Français 🇫🇷", "العربية 🇲🇦"],
    index=0 if lang == "fr" else 1,
)
# Changement → st.rerun()
```

Stocké dans `st.session_state.lang`. Persiste pendant toute la session.

### CSS RTL (injection automatique si `lang == "ar"`)

```python
if lang == "ar":
    st.markdown("""<style>
    .stChatMessage p, .stChatMessage li { direction: rtl; text-align: right; }
    .stMarkdown p, .stMarkdown li      { direction: rtl; text-align: right; }
    .stCaption                          { direction: rtl; text-align: right; }
    </style>""", unsafe_allow_html=True)
```

### Labels i18n

Toutes les étiquettes UI passent par `t(key, lang)` :
```python
st.markdown(f"**📊 {t('sidebar_progress', lang)}**")
st.title(f"🇲🇦 {t('app_title', lang)}")
st.success(f"✅ {t('completion_msg', lang)}")
st.download_button(label=t("pdf_download", lang), ...)
user_input = st.chat_input(t("chat_placeholder", lang))
```

### PDF bilingue

Le bouton de téléchargement génère maintenant un PDF 2 pages (FR + AR) via `BilingualPDFGenerator.generate_bilingual()`.

---

## 5. Librairies ajoutées

### `arabic-reshaper` (v3.0.1)

Regroupe les glyphes arabes isolés en ligatures correctes. Sans reshaper, chaque lettre arabe est affichée de manière isolée, ce qui est illisible.

```python
import arabic_reshaper
text = arabic_reshaper.reshape("مرحبا")  # "مرحبا" → glyphes connectés
```

### `python-bidi` (v0.6.9)

Implémente l'algorithme Unicode Bidirectional (UBA). Transforme l'ordre logique des caractères arabes en ordre visuel pour les systèmes qui ne gèrent pas natvement le RTL.

```python
from bidi.algorithm import get_display
display = get_display(reshaped)  # ordre visuel RTL
```

---

## 6. Tests Jour 6

### `test_i18n.py` — 27 tests

| Groupe | Tests |
|---|---|
| Structure | both_langs, all_fr_in_ar, all_ar_in_fr, no_empty_fr, no_empty_ar |
| `t()` | default_fr, explicit_fr, ar, fallback_lang, unknown_key |
| Clés critiques | 11 clés × 2 langs (paramétrisé) |
| `PROCEDURE_TITLES_AR` | 5 entrées, non-vides |
| `STEP_STATUS_AR` | 4 entrées, non-vides |
| `SUPPORTED_LANGS` | fr + ar présents |

### `test_pdf_bilingual.py` — 8 tests

| Test | Vérifie |
|---|---|
| `test_returns_bytes` | `bytes` |
| `test_valid_pdf_header` | `%PDF` |
| `test_larger_than_french_only` | Page AR ajoute du contenu |
| `test_accepts_empty_info` | Pas d'erreur si `{}` |
| `test_accepts_empty_plan` | Pas d'erreur si `[]` |
| `test_accepts_session_id` | UUID complet OK |
| `test_all_procedure_ids_work` | 5 procédures × AR |
| `test_all_step_statuses_arabic` | 4 statuts × AR |

---

## 7. Résultats tests Jour 6

```
uv run pytest tests/ -v
→ 121 passed in 3.51s ✅

  test_doc_gen.py         :  9 tests ✅
  test_i18n.py            : 27 tests ✅
  test_pdf_bilingual.py   :  8 tests ✅
  test_planner.py         : 25 tests ✅
  test_rag.py             : 13 tests ✅
  test_recommender.py     : 23 tests ✅
  test_session_manager.py : 16 tests ✅
```

---

## 8. Livrables Jour 6

- `services/i18n.py` — 60 traductions FR/AR + PROCEDURE_TITLES_AR + STEP_STATUS_AR
- `tools/pdf_bilingual.py` — BilingualPDFGenerator (Arabic TTF + reshaper + bidi)
- `app.py` — Sélecteur langue + CSS RTL + labels i18n + PDF bilingue
- `tests/test_i18n.py` — 27 tests
- `tests/test_pdf_bilingual.py` — 8 tests
- `docs/JOUR6.md` — Documentation

---

## 9. Commandes utiles

```powershell
uv run pytest tests/ -v
uv run streamlit run app.py
```

---

*Fin de la documentation Jour 6*
