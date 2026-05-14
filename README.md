# 🇲🇦 MAA — Morocco Administrative Agent

[![CI](https://github.com/zairi-yassine/AdminIA/actions/workflows/ci.yml/badge.svg)](https://github.com/zairi-yassine/AdminIA/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Tests](https://img.shields.io/badge/tests-142%20passed-brightgreen)
![MLflow](https://img.shields.io/badge/MLflow-tracking-orange)

> **PFA · Master Data & IA · EMSI Casablanca · 2026**  
> Étudiant : **Yassine Zairi**

---

## 📋 Présentation

**MAA** (Morocco Administrative Agent) guide les citoyens et entrepreneurs marocains pas-à-pas dans leurs démarches administratives grâce à un agent IA local suivant le pattern **ReAct**.

- 🤖 LLM local via **Ollama** (llama3.2 / mistral)
- 📚 Base de connaissance JSON — 5 procédures, 27 documents
- 🔍 Retrieval-Augmented Generation (**RAG**) avec ChromaDB
- 💾 Sessions persistantes via **SQLite**
- 📄 Export **PDF bilingue FR/AR**
- 📊 Tracking des métriques via **MLflow**
- 🌍 Interface bilingue **Français / العربية**

### Procédures couvertes

| ID        | Procédure                               | Durée est. |
| --------- | --------------------------------------- | ---------- |
| `sarl_au` | Création SARL à Associé Unique          | 2–4 sem.   |
| `cnss`    | Immatriculation employeur CNSS          | 1–2 sem.   |
| `ompic`   | Dépôt de marque à l'OMPIC               | 2–3 sem.   |
| `dgi`     | Obtention de l'Identifiant Fiscal (DGI) | 3–7 jours  |
| `rc`      | Inscription au Registre de Commerce     | 1–2 sem.   |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  L1 — Présentation    app.py (Streamlit · bilingue FR/AR)│
├─────────────────────────────────────────────────────────┤
│  L2 — Agent           AgentCore · Planner · Context      │
│                       ReAct 5 phases : routing →         │
│                       recommandation → confirmation →     │
│                       collecte → complétion               │
├─────────────────────────────────────────────────────────┤
│  L3 — Services        LLM · KBLoader · RAGService        │
│                       SessionManager · MLflowTracker     │
│                       i18n · BilingualPDFGenerator       │
├─────────────────────────────────────────────────────────┤
│  L4 — Connaissance    data/kb/ — 5 procédures JSON       │
│                       (27 docs indexés dans ChromaDB)    │
├─────────────────────────────────────────────────────────┤
│  L5 — Persistance     SQLite (sessions) · ChromaDB       │
│                       (vecteurs) · MLflow (métriques)    │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Prérequis

- [uv](https://github.com/astral-sh/uv) ≥ 0.4
- **Option 1** : [Ollama](https://ollama.com) installé et en cours d'exécution (LLM local)
- **Option 2** : Clé API [Groq](https://console.groq.com) (LLM distant ultra-rapide)
- **Option 3** : Clé API [OpenRouter](https://openrouter.ai) (LLM distant)
- Python 3.12+ (géré automatiquement par uv)

---

## 🚀 Installation

```powershell
# 1. Cloner le dépôt
git clone https://github.com/zairi-yassine/AdminIA.git
cd AdminIA

# 2. Installer les dépendances
uv sync

# 3. Configurer l'environnement
Copy-Item .env.example .env
# Éditer .env pour choisir le provider LLM :
#   LLM_PROVIDER=groq    # ou ollama | openrouter
#   LLM_MODEL=llama-3.3-70b-versatile  # modèle Groq

# 4. Si Ollama : télécharger le modèle
ollama pull llama3.2
```

## ▶️ Lancement

```powershell
# Si Ollama : Terminal 1 — Laisser ouvert
ollama serve

# Terminal 2 — Application web
uv run streamlit run app.py
# → http://localhost:8501

# Terminal 3 (optionnel) — Dashboard MLflow
uv run mlflow ui --backend-store-uri sqlite:///data/mlflow.db
# → http://localhost:5000
```

---

## 🧪 Tests

```powershell
uv run pytest tests/ -v
# → 142 passed ✅
```

| Suite de tests            | Tests   | Couverture               |
| ------------------------- | ------- | ------------------------ |
| `test_planner.py`         | 25      | Planner + StepStatus     |
| `test_recommender.py`     | 23      | Moteur de recommandation |
| `test_i18n.py`            | 27      | Traductions FR/AR        |
| `test_mlflow_tracker.py`  | 21      | MLflowTracker lifecycle  |
| `test_rag.py`             | 13      | RAGService + ChromaDB    |
| `test_session_manager.py` | 16      | SQLite persistence       |
| `test_doc_gen.py`         | 9       | PDFGenerator             |
| `test_pdf_bilingual.py`   | 8       | BilingualPDFGenerator    |
| **Total**                 | **142** | **100 %**                |

---

## 📁 Structure du projet

```
MAA/
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions CI (Python 3.12 / 3.13)
├── agent/
│   ├── core.py                 # AgentCore — boucle ReAct 5 phases
│   ├── planner.py              # Planner — orchestration KB-driven
│   └── context.py              # ContextManager — mémoire session
├── services/
│   ├── llm.py                  # LLMService — Ollama / OpenRouter
│   ├── kb_loader.py            # KBLoader — 5 procédures JSON
│   ├── rag.py                  # RAGService — ChromaDB (Jour 5)
│   ├── session_manager.py      # SessionManager — SQLite (Jour 3)
│   ├── recommender.py          # Recommender — profil juridique (Jour 2)
│   ├── i18n.py                 # Traductions FR/AR (Jour 6)
│   └── mlflow_tracker.py       # MLflowTracker (Jour 7)
├── tools/
│   ├── doc_gen.py              # PDFGenerator — résumé FR (Jour 4)
│   └── pdf_bilingual.py        # BilingualPDFGenerator — FR+AR (Jour 6)
├── data/
│   ├── kb/                     # 5 procédures JSON (27 documents)
│   ├── db.py                   # Initialisation SQLite
│   ├── sessions.db             # Base de données sessions (git-ignoré)
│   ├── vectors/                # Embeddings ChromaDB (git-ignoré)
│   └── mlflow.db               # Métriques MLflow (git-ignoré)
├── tests/                      # 142 tests unitaires
├── docs/                       # Documentation par jour (JOUR1 → JOUR8)
├── app.py                      # Interface Streamlit bilingue
├── pyproject.toml              # Dépendances (uv)
└── requirements.txt            # Dépendances pip
```

---

## 🌍 Variables d'environnement

Créer un fichier `.env` à la racine :

```env
LLM_PROVIDER=ollama          # ollama | openrouter
LLM_MODEL=llama3.2           # llama3.2 | mistral | ...
OPENROUTER_API_KEY=          # requis uniquement si LLM_PROVIDER=openrouter
```

---

## 📊 Métriques du projet (8 jours)

| Jour | Livrable                                           | Tests cumulés |
| ---- | -------------------------------------------------- | ------------- |
| J1   | KBLoader + Planner + SQLite + Streamlit v0.1       | 25            |
| J2   | Recommender + ContextManager + SessionManager v0.2 | 64            |
| J3   | Multi-sessions SQLite + Sidebar + App v0.3         | 80            |
| J4   | PDFGenerator + fpdf2 + App v0.4                    | 89            |
| J5   | RAGService + ChromaDB + App v0.5                   | 102           |
| J6   | i18n FR/AR + BilingualPDF + RTL + App v0.6         | 121           |
| J7   | MLflowTracker + Dashboard + App v0.7               | 142           |
| J8   | CI/CD GitHub Actions + README + Docs finale        | 142           |

---

## 📄 Licence

Projet académique — EMSI Casablanca 2026.  
Tous droits réservés © Yassine Zairi.
