# Documentation Jour 7 — MLflow Tracking (Dashboard Métriques)

> **Date** : 12 Mai 2026  
> **Livrable** : MLflow intégré — tracking complet des sessions agent + dashboard UI

---

## 1. Ce qui a été ajouté

### Fichiers créés

| Fichier | Description |
|---|---|
| `services/mlflow_tracker.py` | `MLflowTracker` — tracking sessions + métriques |
| `tests/test_mlflow_tracker.py` | 21 tests |

### Fichiers modifiés

| Fichier | Changement |
|---|---|
| `agent/core.py` | Import + init `MLflowTracker` + hooks dans `respond()` + `reset()` |
| `pyproject.toml` | +`mlflow>=2.12.0` |
| `requirements.txt` | idem |
| `.gitignore` | +`data/mlflow.db`, `mlruns/` |

---

## 2. `services/mlflow_tracker.py`

### API

```python
class MLflowTracker:
    def __init__(tracking_uri="sqlite:///data/mlflow.db")

    # Cycle de vie session
    def start_session(session_id, procedure_id=None, lang="fr", llm_model="llama3.2") -> str
    def end_session(completed=False)

    # Métriques par appel
    def log_response(response_time_ms, intent=None, step=0)
    def log_progress(progress, steps_done, steps_total, step=0)

    # État
    def is_active() -> bool
    def run_id() -> str | None
```

### Backend

```
sqlite:///data/mlflow.db   ← tracking local (git-ignoré)
mlruns/                    ← artifacts MLflow (git-ignoré)
Experiment : "maa_agent"
Run name   : "session_{session_id[:8]}"
```

---

## 3. Ce qui est tracké

### Paramètres (par session)

| Paramètre | Valeur exemple |
|---|---|
| `procedure_id` | `"sarl_au"` |
| `llm_model` | `"llama3.2"` |

### Tags (par session)

| Tag | Valeur exemple |
|---|---|
| `session_id` | `"a1b2c3d4-..."` |
| `lang` | `"fr"` ou `"ar"` |

### Métriques (par appel, avec `step`)

| Métrique | Description |
|---|---|
| `response_time_ms` | Latence totale de `respond()` (LLM inclus) |
| `intent_detected` | 1 si intent ≠ unknown, 0 sinon |
| `progress` | Taux de complétion (0.0 → 1.0) |
| `steps_done` | Nombre d'étapes complétées |
| `steps_total` | Nombre d'étapes total |

### Métriques (fin de session)

| Métrique | Description |
|---|---|
| `session_duration_s` | Durée totale de la session (secondes) |
| `session_completed` | 1 si procédure terminée, 0 sinon |

---

## 4. Intégration dans `agent/core.py`

### Initialisation

```python
self.tracker:        MLflowTracker = MLflowTracker()
self._call_count:    int           = 0
```

### Démarrage (1er appel `respond()`)

```python
self.tracker.start_session(
    self.session_id,
    lang=getattr(self, "_lang", "fr"),
    llm_model=self.llm.model,
)
```

### Par appel (dans `respond()`)

```python
_t0 = time.perf_counter()
# ... logique agent ...
_elapsed_ms = (time.perf_counter() - _t0) * 1000
self._call_count += 1

self.tracker.log_response(
    response_time_ms=_elapsed_ms,
    intent=self.context.procedure_id,
    step=self._call_count,
)
if self.planner.plan:
    self.tracker.log_progress(
        progress=self.planner.progress(),
        steps_done=int(...), steps_total=len(...),
        step=self._call_count,
    )
```

### Fin (dans `reset()`)

```python
self.tracker.end_session(completed=self.planner.is_complete())
```

Tous les appels MLflow sont dans des `try/except` → l'agent fonctionne normalement si MLflow est indisponible.

---

## 5. Dashboard MLflow

### Lancer le dashboard

```powershell
uv run mlflow ui --backend-store-uri sqlite:///data/mlflow.db
# → http://localhost:5000
```

### Ce qu'on voit dans le dashboard

```
Experiment : maa_agent
├── Run: session_a1b2c3d4   [sarl_au | fr | llama3.2]
│   ├── response_time_ms : [450, 380, 290, ...]  (par step)
│   ├── progress         : [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
│   ├── steps_done       : [0, 1, 2, 3, 4, 5]
│   ├── session_duration_s : 342.5
│   └── session_completed  : 1
├── Run: session_b2c3d4e5   [cnss | fr]
│   ├── response_time_ms : [520, 410]
│   ├── progress         : [0.0, 0.25]
│   └── session_completed  : 0    ← session abandonnée
└── ...
```

---

## 6. Tests Jour 7 — `test_mlflow_tracker.py` (21 tests)

Chaque test utilise un fichier SQLite isolé dans `tmp_path` :

```python
@pytest.fixture
def tracker(tmp_path):
    uri = f"sqlite:///{tmp_path}/test_mlflow.db"
    return MLflowTracker(tracking_uri=uri)
```

| Groupe | Tests |
|---|---|
| État initial | `not_active`, `run_id_none`, `experiment_name_constant` |
| `start_session()` | `returns_run_id`, `is_active`, `run_id_set`, with `procedure_id`, `lang`, `llm_model` |
| `end_session()` | `not_active_after`, `run_id_none_after`, `completed_true`, `completed_false`, `no_error_sans_run` |
| `log_response()` | `no_error`, `sans_run`, `unknown_intent` |
| `log_progress()` | `no_error`, `sans_run`, `complete` |
| Replay | `new_session_after_end` |

---

## 7. Résultats tests Jour 7

```
uv run pytest tests/ -q
→ 142 passed in 36.04s ✅

  test_doc_gen.py          :  9 tests ✅
  test_i18n.py             : 27 tests ✅
  test_mlflow_tracker.py   : 21 tests ✅
  test_pdf_bilingual.py    :  8 tests ✅
  test_planner.py          : 25 tests ✅
  test_rag.py              : 13 tests ✅
  test_recommender.py      : 23 tests ✅
  test_session_manager.py  : 16 tests ✅
```

---

## 8. Livrables Jour 7

- `services/mlflow_tracker.py` — MLflowTracker (8 métriques, 2 params, 2 tags)
- `agent/core.py` — hooks timing + tracking dans `respond()` + `reset()`
- `tests/test_mlflow_tracker.py` — 21 tests (SQLite isolé par test)
- `.gitignore` — mlflow.db + mlruns/ exclus
- `docs/JOUR7.md` — Documentation

---

## 9. Commandes utiles

```powershell
uv run pytest tests/ -q
uv run streamlit run app.py
uv run mlflow ui --backend-store-uri sqlite:///data/mlflow.db
```

---

*Fin de la documentation Jour 7*
