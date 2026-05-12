# MAA — Session de Travail Jour 1 à Jour 5

## Documentation Complète de la Conversation

> **Date** : 12 Mai 2026  
> **Étudiant** : Yassine Zairi — Master Data & IA, EMSI Casablanca  
> **Projet** : MAA (Morocco Administrative Agent) — PFA  
> **Stack** : Python 3.14 · Streamlit · Ollama · LLaMA 3.2 · Mistral 7B · SQLite · ChromaDB · MLflow

---

## Table des Matières

1. [Contexte de départ](#1-contexte-de-départ)
2. [Lecture du fichier de référence](#2-lecture-du-fichier-de-référence)
3. [Jour 1 — Implémentation complète](#3-jour-1--implémentation-complète)
4. [Explication du pipeline](#4-explication-du-pipeline)
5. [Jour 2 — Smart Recommendations](#5-jour-2--smart-recommendations)
6. [Git — Nettoyage et push](#6-git--nettoyage-et-push)
7. [Décisions techniques prises](#7-décisions-techniques-prises)
8. [Jour 3 — Multi-Sessions Persistantes + Streamlit Polish](#8-jour-3--multi-sessions-persistantes--streamlit-polish)
9. [Jour 4 — Export PDF + App v0.5](#9-jour-4--export-pdf--app-v05)
10. [Jour 5 — RAG + ChromaDB](#10-jour-5--rag--chromadb)
11. [État final du projet](#11-état-final-du-projet)

---

## 1. Contexte de départ

### Fichiers existants (avant la session)

Le projet avait déjà une structure vide créée :

```
MAA/
├── agent/
│   ├── __init__.py    (vide)
│   ├── context.py     (vide)
│   ├── core.py        (vide)
│   └── planner.py     (vide)
├── services/
│   ├── __init__.py    (vide)
│   ├── llm.py         (existant, avec garbage lignes 65-66)
│   └── rag.py         (vide)
├── tools/
│   ├── __init__.py    (vide)
│   └── doc_gen.py     (vide)
├── tests/
│   └── test_planner.py (vide)
├── app.py              (vide)
├── .env                (LLM_PROVIDER=ollama, LLM_MODEL=llama3.2)
├── requirements.txt
└── pyproject.toml
```

### Problème identifié dans `services/llm.py`

Les lignes 65-66 contenaient des tokens garbage :

```python
# AVANT (cassé)
    def change_model(self, model_name: str):
        self.model = model_name
        print(f"Modèle changé : {model_name}")

        34302072
        b7ff23ff100a5e78a4a65b88213a3ffd  ← tokens inutiles supprimés
```

---

## 2. Lecture du fichier de référence

Le fichier `MAA_conversation_complete.md` a été lu intégralement. Il contient :

- L'architecture 5 couches (L1 à L5)
- Les codes sources complets pour chaque module
- Le planning 10 jours
- Les décisions techniques
- L'arbre de décision Smart Recommendations

**Planning retenu :**

| Jour            | Phase                      | Livrable soir               |
| --------------- | -------------------------- | --------------------------- | --- |
| **Lundi S1**    | Knowledge Base + LLM       | 5 JSON + Planner lit KB     |
| **Mardi S1**    | Agent ReAct complet        | CLI fonctionnel + Smart Rec |
| **Mercredi S1** | Multi-sessions + Streamlit | UI + sessions persistantes  | ✅  |
| **Jeudi S1**    | Polish + Export PDF        | App complète v0.5           | ✅  |
| **Lundi S2**    | RAG + ChromaDB             | Zéro hallucination          | ✅  |
| Mardi S2        | PDF formulaires + Arabe    | PDF pré-rempli + bilingue   |
| Mercredi S2     | MLflow + 20 tests          | Dashboard + métriques       |
| Jeudi S2        | Rapport + Démo             | Projet 100% livré           |

---

## 3. Jour 1 — Implémentation complète

### 3.1 Fichiers créés

#### `data/kb/sarl_au.json`

5 étapes — Frais : 3000–5000 MAD — Durée : 2 à 4 semaines

| Étape                               | Organisme             | Frais    |
| ----------------------------------- | --------------------- | -------- |
| 1. Profil du fondateur              | —                     | 0 MAD    |
| 2. Capital et siège social          | —                     | 0 MAD    |
| 3. Certificat Négatif OMPIC         | OMPIC                 | 170 MAD  |
| 4. Statuts notariés + dépôt capital | Notaire + Banque      | 2000 MAD |
| 5. Immatriculation RC + DGI + CNSS  | Tribunal / DGI / CNSS | 350 MAD  |

**Chaque étape contient :**

- `infos_requises` — clés des champs à collecter
- `labels_infos` — questions en langage naturel (affiché à l'utilisateur)
- `docs_requis` — liste des documents nécessaires
- `frais` — coût en MAD
- `delai` — durée estimée
- `lien_officiel` — URL officielle

#### `data/kb/cnss.json`

4 étapes — Frais : 0 MAD — Durée : 3 à 5 jours

#### `data/kb/ompic.json`

5 étapes — Frais : 650 MAD/classe — Durée : 12 à 18 mois

#### `data/kb/dgi.json`

4 étapes — Frais : 0 MAD — Durée : 1 à 3 jours

#### `data/kb/rc.json`

4 étapes — Frais : 350 MAD — Durée : 3 à 7 jours

---

#### `data/__init__.py`

Package Python pour le module data.

#### `data/db.py`

Initialisation SQLite avec les 4 tables du schéma :

```python
def init_db():
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           TEXT PRIMARY KEY,
            created_at   DATETIME NOT NULL,
            updated_at   DATETIME NOT NULL,
            procedure_id TEXT,
            status       TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS collected_info (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL REFERENCES sessions(id),
            step_id     INTEGER NOT NULL,
            field_key   TEXT NOT NULL,
            field_value TEXT NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS steps_progress (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT NOT NULL REFERENCES sessions(id),
            step_id      INTEGER NOT NULL,
            step_title   TEXT NOT NULL,
            status       TEXT DEFAULT 'pending',
            started_at   DATETIME,
            completed_at DATETIME
        );
    """)
```

---

#### `services/kb_loader.py`

```python
class KBLoader:
    def load_procedure(self, procedure_id: str) -> dict
    def list_procedures(self) -> list[dict]
    def get_procedure_summary(self, procedure_id: str) -> str
    def detect_intent(self, message: str) -> str
```

Détection d'intention par keywords (dict ordonné, spécifique avant générique) :

- `sarl_au`, `cnss`, `ompic`, `dgi`, `rc`, `recommandation`, `unknown`

---

#### `agent/context.py`

```python
class ContextManager:
    def add_message(self, role: str, content: str)
    def update_info(self, key: str, value: str)
    def get_history_for_llm(self) -> list[dict]
    def get_collected_info(self) -> str
    def reset()
```

**Rôle critique :** Streamlit ré-exécute tout le script à chaque message. Sans `ContextManager` stocké dans `st.session_state`, l'agent oublie tout.

---

#### `agent/planner.py` — KB-driven

Design Jour 1 vs design doc :

| Ancien (doc)                    | Nouveau (implémenté)                     |
| ------------------------------- | ---------------------------------------- |
| `PLANS` hardcodé dans la classe | Charge depuis `data/kb/*.json`           |
| Pas de labels humains           | `missing_info_label()` → question claire |
| Pas de docs par étape           | `get_current_step_docs()`                |
| Pas de frais totaux             | `get_total_fees()`                       |

```python
class StepStatus(Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    BLOCKED     = "blocked"

class Planner:
    def create_plan(self, procedure_id: str) -> list[dict]
    def current_step(self) -> dict | None
    def missing_info(self) -> str | None
    def missing_info_label(self) -> str | None  # AJOUT
    def record_info(self, key: str, value: str)
    def progress(self) -> float
    def is_complete(self) -> bool
    def plan_summary(self) -> str
    def get_total_fees(self) -> int  # AJOUT
```

---

#### `agent/core.py` — ReAct (version Jour 1)

```python
class AgentCore:
    def respond(self, user_message: str) -> str
    def _handle_first_message(self, message: str) -> str   # routing
    def _handle_collection(self, message: str) -> str      # collecte
    def _handle_completion(self) -> str                    # finalisation
    def reset()
```

---

#### `app.py` — Streamlit UI

```python
# Initialisation session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = AgentCore()

# Sidebar : progression + plan + liste procédures
# Main : chat interface
# Input : st.chat_input()
```

---

### 3.2 Résultats des tests Jour 1

```
uv run pytest tests/test_planner.py -v
→ 25 passed in 0.24s ✅

uv run python test_agent.py
→ TEST 1 KBLoader  : ✅ 5 procédures, 6/6 intents corrects
→ TEST 2 Planner   : ✅ Plan créé, collecte simulée 80%
→ TEST 3 SQLite DB : ✅ 4 tables initialisées
→ TEST 4 Agent+LLM : ✅ Conversation Ollama fonctionnelle
```

---

## 4. Explication du pipeline

### 4.1 Flux général

```
User (input texte)
    ↓
app.py (Streamlit)      → délègue tout, pas de logique métier
    ↓
AgentCore.respond()     → dispatcher des phases
    ↓
KBLoader.detect_intent() → détermine quelle procédure
    ↓
Planner.create_plan()   → charge JSON depuis data/kb/
    ↓
LLMService.chat()       → génère la réponse en français
    ↓ (boucle)
Planner.missing_info()  → quel champ collecter ?
    ↓
ContextManager.update() → stocke l'info
    ↓
Planner.record_info()   → avance dans l'étape
```

### 4.2 Pourquoi chaque choix

| Choix             | Raison                                               |
| ----------------- | ---------------------------------------------------- |
| JSON pour la KB   | Lisible, modifiable sans code, versionnable          |
| KB-driven Planner | Ajouter une procédure = 1 fichier JSON, 0 code       |
| SQLite            | Sans serveur, portable, idéal démo jury              |
| Streamlit         | Zéro HTML/CSS, 1 commande pour lancer                |
| Ollama local      | Gratuit, offline, zéro quota, idéal démo             |
| ReAct pattern     | Observable, explicable, testable                     |
| 5 couches         | Séparation responsabilités, testabilité indépendante |

---

## 5. Jour 2 — Smart Recommendations

### 5.1 Nouveau fichier : `services/recommender.py`

#### `LEGAL_STATUS_INFO`

4 statuts complets avec avantages, inconvénients, lien officiel, et mapping vers procédure MAA :

| Statut              | Procédure MAA  |
| ------------------- | -------------- |
| `auto_entrepreneur` | `None` (KB v2) |
| `sarl_au`           | `"sarl_au"` ✅ |
| `sarl`              | `None` (KB v2) |
| `sa`                | `None` (KB v2) |

#### `Recommender` — Classe

```python
class Recommender:
    def get_next_question(self) -> tuple[str, str] | None
    def record(self, key: str, value: str)
    def is_profile_complete(self) -> bool
    def analyze(self) -> dict          # arbre de décision
    def format_recommendation(self) -> str
    def reset()
```

**4 questions posées :**

1. `nb_associes` — nombre de fondateurs
2. `ca_previsionnel` — CA annuel prévisionnel (MAD)
3. `type_activite` — service / commerce / artisanat / industrie
4. `capital_disponible` — capital de départ (MAD)

#### Arbre de décision

```python
if nb == 1:
    if ca < 500_000 and activite in ("service", "artisanat"):
        → "auto_entrepreneur"
    else:
        → "sarl_au"
elif nb >= 5 and capital >= 300_000:
    → "sa"
elif nb >= 2:
    → "sarl"
```

**Pourquoi un arbre de décision et pas le LLM ?**

- **Déterministe** — même profil = même recommandation (testable)
- **Fiable** — pas d'hallucination sur les seuils légaux (500K MAD, 300K MAD)
- Le LLM est utilisé uniquement pour **présenter** la recommandation, pas pour la **calculer**

---

### 5.2 Mise à jour `services/kb_loader.py`

Ajout de l'intent `recommandation` :

```python
"recommandation": [
    "créer une entreprise", "créer mon entreprise",
    "quelle forme juridique", "quel statut juridique",
    "aide moi à choisir", "quel est le meilleur statut",
    ...
]
```

**Ordre important :** `recommandation` est en dernier dans le dict. Les intents spécifiques (`sarl_au`, `cnss`…) sont vérifiés en premier → pas de conflit.

---

### 5.3 Mise à jour `agent/core.py` — 5 phases

#### Nouveaux flags

```python
class AgentCore:
    self.recommender:        Recommender    = Recommender()      # NOUVEAU
    self._in_recommendation: bool           = False              # NOUVEAU
    self._pending_procedure: str | None     = None               # NOUVEAU
```

#### Dispatcher mis à jour

```python
def respond(self, user_message: str) -> str:
    if self._in_recommendation:             # Phase 1 (NOUVEAU)
        → _handle_recommendation_collection()
    elif self._pending_procedure:            # Phase 2 (NOUVEAU)
        → _handle_procedure_confirmation()
    elif not self.planner.plan:             # Phase 0
        → _handle_first_message()
    elif not self.planner.is_complete():    # Phase 3
        → _handle_collection()
    else:                                   # Phase 4
        → _handle_completion()
```

#### Phase 1 — Collecte profil

```python
def _handle_recommendation_collection(self, message: str) -> str:
    # 1. Enregistre la réponse à la question courante
    self.recommender.record(key, message)

    # 2. Profil complet ?
    if self.recommender.is_profile_complete():
        result = self.recommender.analyze()
        if result["procedure_id"]:
            self._pending_procedure = result["procedure_id"]  # → Phase 2
        # LLM présente la recommandation

    # 3. Sinon, poser la question suivante
    else:
        # LLM pose la question suivante
```

#### Phase 2 — Confirmation

```python
def _handle_procedure_confirmation(self, message: str) -> str:
    _POSITIVE_WORDS = {"oui", "ok", "d'accord", "allons-y", ...}

    if confirmed:
        self.planner.create_plan(procedure_id)  # → Phase 3
    else:
        self._pending_procedure = None           # → attente
```

---

### 5.4 Flux de conversation complet Jour 2

```
👤 "je veux créer une entreprise"
   → intent = "recommandation"
   → _in_recommendation = True

🤖 "Pour vous recommander le meilleur statut, 4 questions.
    Combien de fondateurs ?"

👤 "1"  → nb_associes = 1
🤖 "Quel CA prévisionnel en MAD ?"

👤 "200000"  → ca = 200000
🤖 "Quel type d'activité ?"

👤 "service"  → type = service
🤖 "Quel capital disponible ?"

👤 "5000"  → capital = 5000
   → is_profile_complete() = True
   → analyze() → "auto_entrepreneur"
   → procedure_id = None (pas encore dans KB)

🤖 "Je recommande : Auto-Entrepreneur.
    Avantages : création en 24h, zéro charge...
    Ce statut sera bientôt dans MAA."

--- Autre cas : CA > 500K ---

👤 "800000"  → ca = 800000
   → analyze() → "sarl_au"
   → _pending_procedure = "sarl_au"

🤖 "Je recommande : SARL AU.
    Voulez-vous que je vous guide dans la procédure ?"

👤 "oui"
   → confirmed = True
   → planner.create_plan("sarl_au")
   → Phase 3 démarre

🤖 "Parfait ! Plan SARL AU en 5 étapes.
    Commençons : votre nom complet ?"
```

---

### 5.5 Résultats des tests Jour 2

```
uv run pytest tests/ -v
→ 48 passed in 0.16s ✅

  test_planner.py     : 25 tests ✅
  test_recommender.py : 23 tests ✅
```

---

## 6. Git — Nettoyage et push

### 6.1 Fichiers exclus du repo (`.gitignore` mis à jour)

```gitignore
.env                      # variables d'environnement (secrets)
data/sessions.db          # base runtime (générée au lancement)
data/vectors/             # embeddings ChromaDB (régénérables)
test_agent.py             # script CLI de debug
test_llm.py               # script de test dev
workspace.code-workspace  # fichier IDE personnel
MAA_conversation_complete.md  # log de conversation
```

### 6.2 `.env.example` créé

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# OPENROUTER_API_KEY=sk-or-...
```

### 6.3 Commits

```
Jour 1 : 22 files changed, 1317 insertions(+)
  → Knowledge Base + Agent + Streamlit + SQLite

Jour 2 : 6 files changed, 1209 insertions(+)
  → Smart Recommendations + Agent ReAct complet
```

---

## 7. Décisions techniques prises

### Décisions Jour 1

| Décision                        | Alternative rejetée | Raison du choix                      |
| ------------------------------- | ------------------- | ------------------------------------ |
| KB-driven Planner               | PLANS hardcodé      | Ajouter procédure = 1 JSON, 0 code   |
| `labels_infos` dans JSON        | Labels dans le code | Modifiable sans redéploiement        |
| `detect_intent()` dans KBLoader | Dans AgentCore      | KBLoader connaît la KB, pas l'agent  |
| `init_db()` dans `app.py`       | Script séparé       | Garantit l'init au premier lancement |

### Décisions Jour 2

| Décision                           | Alternative rejetée  | Raison du choix                              |
| ---------------------------------- | -------------------- | -------------------------------------------- |
| Arbre de décision Python           | LLM pour recommander | Déterministe, testable, pas d'hallucination  |
| `_pending_procedure` flag          | Démarrer directement | UX : confirmation explicite de l'utilisateur |
| `Recommender` séparé de `Planner`  | Une seule classe     | Responsabilités distinctes (SRP)             |
| Intent `recommandation` en dernier | En premier           | Évite les conflits avec intents spécifiques  |

---

## 8. Jour 3 — Multi-Sessions Persistantes + Streamlit Polish

### 8.1 Nouveau fichier : `services/session_manager.py`

CRUD complet sur les 4 tables SQLite — 12 méthodes :

```python
class SessionManager:
    # Sessions
    def create_session(procedure_id=None) -> str   # UUID v4
    def update_session(session_id, **kwargs)
    def get_session(session_id) -> dict | None
    def list_sessions(limit=10) -> list[dict]      # triées updated_at DESC
    def close_session(session_id)                  # status -> "closed"

    # Messages
    def save_message(session_id, role, content)
    def get_messages(session_id) -> list[dict]

    # Collected info
    def save_collected_info(session_id, step_id, key, value)
    def get_collected_info(session_id) -> list[dict]

    # Steps progress
    def upsert_step_progress(session_id, step_id, title, status)
    def get_steps_progress(session_id) -> list[dict]
```

### 8.2 Intégration dans `agent/core.py`

#### Nouveaux attributs

```python
class AgentCore:
    self.session_mgr: SessionManager = SessionManager()
    self.session_id:  str | None     = None
```

#### 4 hooks dans `respond()` — persistance complète

```python
def respond(self, user_message):
    if not self.session_id:
        self.session_id = self.session_mgr.create_session()   # 1. créer
    self.session_mgr.save_message(session_id, "user", ...)    # 2. user
    # ... logique ...
    self.session_mgr.save_message(session_id, "assistant", .) # 3. assistant
    self._sync_steps_to_db()                                   # 4. steps
```

Dans `_handle_collection()` : `save_collected_info()` après chaque réponse.
Dans `reset()` : `close_session()` + `session_id = None`.

### 8.3 Sidebar enrichie `app.py`

- **Infos collectées** — clé/valeur affichées en temps réel
- **Session courante** — UUID court (8 chars)
- **Sessions récentes** — 5 dernières (date, procédure, nb msgs, statut actif/fermé)

### 8.4 Tests — 16 tests (`tests/conftest.py` + `tests/test_session_manager.py`)

Fixture `tmp_db` = base SQLite isolée par test via `monkeypatch.setattr(data.db, "DB_PATH", ...)`.

```
64 / 64 tests  (25 planner + 23 recommender + 16 session_manager)
Commit Jour 3 pousse sur GitHub
```

---

## 9. Jour 4 — Export PDF + App v0.5

### 9.1 Nouveau fichier : `tools/doc_gen.py`

```python
class PDFGenerator:
    def generate_summary(
        procedure, collected_info, plan, session_id=""
    ) -> bytes   # PDF valide (%PDF...)
```

**5 sections** : en-tête vert MAA · infos générales · infos collectées · plan des étapes · pied de page.

**Bug fpdf2 résolu** — `_safe()` remplace les caractères hors Latin-1 (`—` U+2014, smart quotes...) avant de passer à Helvetica.

### 9.2 Améliorations `app.py`

- **Banner** `Toutes les informations ont été collectées` + bouton `Télécharger le résumé PDF`
- **Gestion erreur Ollama** — try/except avec message explicite

### 9.3 Tests — 9 tests (`tests/test_doc_gen.py`)

```
73 / 73 tests  (+ 9 doc_gen)
Commit Jour 4 pousse sur GitHub
```

---

## 10. Jour 5 — RAG + ChromaDB

### 10.1 Nouveau fichier : `services/rag.py`

```python
class RAGService:
    def __init__(persist_dir, ephemeral=False, embedding_function=None)
    def index_kb(kb_loader, force=False)              # 27 docs, idempotent
    def query(text, n_results=3, procedure_id=None) -> str
    def is_indexed() -> bool
    def count() -> int
```

**27 documents** = 5 overviews + 22 étapes (5+4+5+4+4).
**Stockage** : `data/vectors/` (PersistentClient, git-ignoré, régénérable).

### 10.2 Intégration dans `agent/core.py`

```python
# __init__
self.rag = RAGService()
try: self.rag.index_kb(self.kb_loader)
except Exception: pass   # non critique

# Phase 0 — procédure détectée
rag_context = self.rag.query(message, n_results=2, procedure_id=procedure_id)
system += f"Documentation officielle :\n{rag_context}\n"

# Phase 4 — finalisation
rag_context = self.rag.query(f"etapes documents {proc['titre']}", n_results=3, ...)
```

**Effet** : frais exacts, délais officiels et documents requis injectés dans le prompt → zéro hallucination KB.

### 10.3 Tests — 13 tests (`tests/test_rag.py`)

`DummyEF` = embeddings SHA-256 déterministes, zéro téléchargement de modèle.

```
86 / 86 tests  (+ 13 rag)
Commit Jour 5 pousse sur GitHub
```

---

## 11. État final du projet (après Jour 5)

### Structure complète

```
MAA/
├── agent/
│   ├── context.py             ✅ ContextManager
│   ├── core.py                ✅ AgentCore (5 phases + RAG + SessionMgr)
│   └── planner.py             ✅ Planner KB-driven
├── services/
│   ├── kb_loader.py           ✅ KBLoader (6 intents)
│   ├── llm.py                 ✅ LLMService (Ollama/OpenRouter)
│   ├── rag.py                 ✅ RAGService (ChromaDB 1.5.7)
│   ├── recommender.py         ✅ Recommender (arbre décision)
│   └── session_manager.py     ✅ SessionManager (CRUD SQLite)
├── data/
│   ├── kb/
│   │   ├── sarl_au.json       ✅ 5 étapes
│   │   ├── cnss.json          ✅ 4 étapes
│   │   ├── ompic.json         ✅ 5 étapes
│   │   ├── dgi.json           ✅ 4 étapes
│   │   └── rc.json            ✅ 4 étapes
│   ├── db.py                  ✅ SQLite init (4 tables)
│   ├── sessions.db            ⏳ runtime (git-ignoré)
│   └── vectors/               ✅ ChromaDB index (git-ignoré)
├── tools/
│   └── doc_gen.py             ✅ PDFGenerator (fpdf2)
├── tests/
│   ├── conftest.py            ✅ fixture tmp_db
│   ├── test_planner.py        ✅ 25 tests
│   ├── test_recommender.py    ✅ 23 tests
│   ├── test_session_manager.py ✅ 16 tests
│   ├── test_doc_gen.py        ✅  9 tests
│   └── test_rag.py            ✅ 13 tests
├── docs/
│   ├── JOUR1.md - JOUR5.md    ✅
├── app.py                     ✅ Streamlit v0.5 (banner + PDF + sessions)
├── README.md                  ✅
└── .env.example               ✅
```

### Métriques cumulées

| Métrique              | Jours 1-2 | Jours 3-5 | Total          |
| --------------------- | --------- | --------- | -------------- |
| Tests unitaires       | 48        | 38        | **86 / 86 ✅** |
| Fichiers Python créés | 10        | 5         | **15**         |
| Phases agent          | 5         | 5         | **5**          |
| Documents ChromaDB    | 0         | 27        | **27**         |
| Commits GitHub        | 2         | 3         | **5**          |

### Prochaines étapes (Jour 6)

```
Jour 6 — Mardi S2 :
  - PDF bilingue Arabe/Francais (polices TTF DejaVu/Amiri)
  - Interface Streamlit RTL/LTR
  - Formulaires pre-remplis
```

---

## 12. Commandes de référence

```powershell
# Avant chaque session de travail
ollama serve                          # Terminal 1 — laisser ouvert

# Lancer l'application
uv run streamlit run app.py           # → http://localhost:8501

# Tests
uv run pytest tests/ -v              # 86 tests

# Git
git add -A
git commit -m "Jour X : ..."
git push origin main
```

---

_Document mis à jour — Session Jours 1 à 5 — MAA · 12 Mai 2026_
