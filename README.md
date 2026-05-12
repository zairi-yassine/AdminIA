# 🇲🇦 MAA — Morocco Administrative Agent

Système agentique d'orientation pour les procédures administratives au Maroc.

> PFA · Master Data & IA · EMSI Casablanca · 2026  
> Étudiant : Yassine Zairi

## Présentation

MAA guide les citoyens et entrepreneurs marocains pas-à-pas dans leurs démarches administratives grâce à un agent IA local (Ollama) suivant le pattern **ReAct**.

### Procédures couvertes

| ID        | Procédure                               |
| --------- | --------------------------------------- |
| `sarl_au` | Création SARL à Associé Unique          |
| `cnss`    | Immatriculation employeur CNSS          |
| `ompic`   | Dépôt de marque à l'OMPIC               |
| `dgi`     | Obtention de l'Identifiant Fiscal (DGI) |
| `rc`      | Inscription au Registre de Commerce     |

## Architecture

```
L1 — Presentation  →  app.py (Streamlit)
L2 — Agent         →  agent/core.py · planner.py · context.py
L3 — Service       →  services/llm.py · kb_loader.py · rag.py
L4 — Knowledge     →  data/kb/*.json
L5 — Data          →  data/sessions.db (SQLite)
```

## Stack technique

`Python 3.14` · `Streamlit` · `Ollama` · `Mistral 7B` · `LLaMA 3.2` · `SQLite` · `ChromaDB` · `MLflow` · `fpdf2`

## Installation

```powershell
# 1. Cloner le dépôt
git clone https://github.com/<user>/MAA.git
cd MAA

# 2. Installer les dépendances (uv requis)
uv sync

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env si nécessaire

# 4. Installer Ollama et télécharger les modèles
# https://ollama.com
ollama pull llama3.2
ollama pull mistral
```

## Lancement

```powershell
# Terminal 1 — Laisser ouvert
ollama serve

# Terminal 2 — Application
uv run streamlit run app.py
# → http://localhost:8501
```

## Tests

```powershell
uv run pytest tests/ -v
```

## Structure du projet

```
MAA/
├── agent/
│   ├── core.py          # AgentCore — boucle ReAct
│   ├── planner.py       # Planner — orchestration KB-driven
│   └── context.py       # ContextManager — mémoire de session
├── services/
│   ├── llm.py           # LLMService — Ollama / OpenRouter
│   ├── kb_loader.py     # KBLoader — chargeur de procédures
│   └── rag.py           # RAGService — ChromaDB (Jour 5)
├── data/
│   ├── kb/              # 5 procédures JSON
│   ├── db.py            # Initialisation SQLite
│   ├── templates/       # Templates PDF (Jour 6)
│   └── vectors/         # Embeddings ChromaDB (Jour 5)
├── tools/
│   └── doc_gen.py       # Génération PDF (Jour 6)
├── tests/
│   └── test_planner.py  # Tests unitaires (25 tests)
└── app.py               # Interface Streamlit
```
