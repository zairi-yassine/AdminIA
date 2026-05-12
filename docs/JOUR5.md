# Documentation Jour 5 — RAG + ChromaDB (Zéro Hallucination)

> **Date** : 12 Mai 2026  
> **Livrable** : RAGService opérationnel — KB indexée dans ChromaDB, contexte injecté dans les prompts

---

## 1. Ce qui a été ajouté

### Fichier implémenté : `services/rag.py`

`RAGService` — indexation de la KB + retrieval par similarité vectorielle.

### Fichiers modifiés

| Fichier | Changement |
|---|---|
| `agent/core.py` | Import + initialisation RAG + injection contexte |

### Nouveaux tests

| Fichier | Tests |
|---|---|
| `tests/test_rag.py` | 13 tests (DummyEF, no download) |

---

## 2. Pourquoi le RAG ?

### Problème sans RAG

Le LLM génère des réponses basées sur ses données d'entraînement (jusqu'à un certain cutoff). Pour des procédures administratives marocaines spécifiques :
- Les frais exacts (170 MAD pour OMPIC, 350 MAD pour RC…) peuvent être hallucines
- Les délais officiels peuvent être incorrects
- Les documents requis peuvent manquer ou être inventes

### Solution avec RAG

```
User query
    ↓
Embed query (all-MiniLM-L6-v2)
    ↓
Recherche vectorielle ChromaDB
    ↓
Top-K chunks pertinents (texte brut des JSON KB)
    ↓
Injection dans le system prompt LLM
    ↓
LLM répond en se basant sur la documentation officielle
    → Zéro hallucination sur les données de la KB
```

---

## 3. `services/rag.py` — Architecture

### Schéma de la collection ChromaDB

```
Collection : maa_kb
├── sarl_au_overview    {procedure_id: "sarl_au", type: "overview", step_id: 0}
├── sarl_au_step_1      {procedure_id: "sarl_au", type: "step",     step_id: 1}
├── sarl_au_step_2      {procedure_id: "sarl_au", type: "step",     step_id: 2}
├── ...
├── cnss_overview       {procedure_id: "cnss",    type: "overview", step_id: 0}
├── cnss_step_1         {procedure_id: "cnss",    type: "step",     step_id: 1}
├── ...
└── rc_step_4           {procedure_id: "rc",      type: "step",     step_id: 4}

Total : 27 documents  (5 overviews + 22 étapes)
```

### Contenu d'un chunk step

```
Etape 3 - Certificat Negatif OMPIC
Procedure : Creation SARL a Associe Unique
Organisme : OMPIC
Description : Verifier la disponibilite de la denomination sociale...
Documents requis : CIN, 170 MAD en especes
Frais : 170 MAD
Delai : 1 a 2 jours ouvrables
Lien officiel : https://www.ompic.ma
```

### API de `RAGService`

```python
class RAGService:
    def __init__(
        persist_dir:        str | None = None,   # defaut: data/vectors/
        ephemeral:          bool       = False,   # in-memory (tests)
        embedding_function: Any | None = None,   # defaut: DefaultEmbeddingFunction
    )
    
    def index_kb(kb_loader, force=False)   # indexe si pas encore fait (idempotent)
    def query(text, n_results=3, procedure_id=None) -> str   # retrieval
    def is_indexed() -> bool
    def count() -> int
```

### Stockage

```
data/vectors/          ← VECTORS_DIR (PersistentClient)
  chroma.sqlite3       ← Index ChromaDB
  <uuid>/              ← Segments HNSW (embeddings)
```

Ce dossier est dans `.gitignore` (régénérable) — les embeddings ne sont pas versionnés.

---

## 4. Intégration dans `agent/core.py`

### Initialisation

```python
class AgentCore:
    def __init__(self):
        ...
        self.rag = RAGService()      # PersistentClient → data/vectors/
        try:
            self.rag.index_kb(self.kb_loader)   # skip si déjà indexé
        except Exception:
            pass   # RAG non critique — agent fonctionne sans
```

Le `try/except` garantit que l'agent démarre même si ChromaDB n'est pas disponible.

### Phase 0 — Routing (procédure détectée)

```python
rag_context = self.rag.query(message, n_results=2, procedure_id=procedure_id)
system = (
    "Tu es MAA..."
    f"Résumé :\n{summary}\n"
    f"Plan :\n{self.planner.plan_summary()}\n"
    + (f"Documentation officielle :\n{rag_context}\n" if rag_context else "")
    + f"Annonce le plan et pose la première question..."
)
```

**Effet** : Le LLM sait exactement quels documents sont requis, les frais exacts, les délais officiels pour chaque étape.

### Phase 4 — Completion

```python
rag_context = self.rag.query(
    f"etapes documents frais {proc.get('titre', '')}",
    n_results=3,
    procedure_id=self.context.procedure_id,
)
```

**Effet** : Le résumé final cite les informations officielles (frais réels, liens officiels, etc.).

---

## 5. Tests Jour 5

### `DummyEF` — Embedding function sans download

```python
class DummyEF(EmbeddingFunction):
    """32-dim hash-based embedding — no model download required."""
    def __call__(self, input: Documents) -> Embeddings:
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()]
            for t in input
        ]
```

**Pourquoi ?** La `DefaultEmbeddingFunction` de ChromaDB (`all-MiniLM-L6-v2`) télécharge un modèle ONNX (~23MB) au premier appel. Ce téléchargement rend les tests lents et fragiles en CI. `DummyEF` produit des embeddings déterministes instantanément.

### Tests couverts — 13 tests

| Groupe | Tests |
|---|---|
| Avant indexation | `is_indexed=False`, `count=0`, `query=""` |
| Indexation | `is_indexed=True`, `count>0`, count exact (27), idempotent, force |
| Requêtes | returns string, non-empty, n_results, filtre procedure_id, 5 procedures |

### Calcul du count attendu

```python
# 5 procédures × (1 overview + N étapes)
sarl_au : 1 + 5 = 6
cnss    : 1 + 4 = 5
ompic   : 1 + 5 = 6
dgi     : 1 + 4 = 5
rc      : 1 + 4 = 5
Total   : 27 documents
```

---

## 6. Flux RAG complet — exemple

```
User : "je veux créer une SARL AU"
  → intent = "sarl_au"
  → rag.query("je veux créer une SARL AU", n_results=2, procedure_id="sarl_au")
  
  Retrieval ChromaDB :
  [1] sarl_au_overview     (distance: 0.12)
  [2] sarl_au_step_3       (distance: 0.31)
  
  Contexte injecté dans le prompt :
  ---
  Procedure : Creation SARL a Associe Unique
  Organismes : OMPIC, Notaire, Tribunal de Commerce, DGI, CNSS
  Duree estimee : 2 a 4 semaines
  ---
  Etape 3 - Certificat Negatif OMPIC
  Frais : 170 MAD
  Lien officiel : https://www.ompic.ma
  ---
  
LLM → réponse basée sur documentation officielle, pas sur ses poids
```

---

## 7. Résultats tests Jour 5

```
uv run pytest tests/ -v
→ 86 passed in 1.92s ✅

  test_doc_gen.py         :  9 tests ✅
  test_planner.py         : 25 tests ✅
  test_rag.py             : 13 tests ✅
  test_recommender.py     : 23 tests ✅
  test_session_manager.py : 16 tests ✅
```

---

## 8. Livrables Jour 5

### Fichiers créés/modifiés
- `services/rag.py` — RAGService (indexing + query + utils)
- `agent/core.py` — RAG intégré (phases 0 et 4)
- `tests/test_rag.py` — 13 tests avec DummyEF
- `docs/JOUR5.md` — Documentation

---

## 9. Commandes utiles

```powershell
uv run pytest tests/ -v
uv run streamlit run app.py
```

---

*Fin de la documentation Jour 5*
