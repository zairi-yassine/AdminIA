# Documentation Jour 1 — Architecture et Flux du Pipeline

> **Date** : 12 Mai 2026  
> **Livrable** : Knowledge Base (5 JSON) + Agent ReAct + Streamlit UI + SQLite

---

## 1. Vue d'ensemble du flux

```
User (input texte)
    ↓
app.py (Streamlit)
    ↓
AgentCore.respond()
    ↓
┌─────────────────────────────────────────┐
│  Phase 1 : Première intention            │
│  ─────────────────────────────────────  │
│  KBLoader.detect_intent(message)         │
│  → "sarl_au" / "cnss" / ... / "unknown" │
│                                          │
│  Planner.create_plan(procedure_id)      │
│  → Charge JSON depuis data/kb/          │
│  → Crée plan d'étapes                    │
│                                          │
│  LLMService.chat()                       │
│  → Génère réponse avec le plan           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Phase 2 : Collecte d'informations      │
│  ─────────────────────────────────────  │
│  Planner.missing_info()                  │
│  → Quel champ est manquant ?             │
│                                          │
│  ContextManager.update_info(key, value)  │
│  → Stocke l'info en mémoire              │
│                                          │
│  Planner.record_info(key, value)         │
│  → Avance dans l'étape                   │
│  → Passe à l'étape suivante si complète │
│                                          │
│  LLMService.chat()                       │
│  → Pose la question suivante             │
└─────────────────────────────────────────┘
    ↓ (répété jusqu'à completion)
┌─────────────────────────────────────────┐
│  Phase 3 : Finalisation                  │
│  ─────────────────────────────────────  │
│  Planner.is_complete() = True           │
│                                          │
│  LLMService.chat()                      │
│  → Résumé complet + prochaines étapes   │
└─────────────────────────────────────────┘
```

---

## 2. Communication détaillée fichier par fichier

### `app.py` → `agent/core.py`

```python
# app.py
from agent.core import AgentCore

# Initialisation (une seule fois, dans st.session_state)
st.session_state.agent = AgentCore()

# À chaque message utilisateur
response = agent.respond(user_input)
```

**Pourquoi ?** `app.py` ne doit pas contenir de logique métier. Il ne fait que l'affichage UI et délègue tout à `AgentCore`. C'est le pattern **separation of concerns**.

---

### `agent/core.py` → `services/kb_loader.py`

```python
# agent/core.py
from services.kb_loader import KBLoader

class AgentCore:
    def __init__(self):
        self.kb_loader = KBLoader()  # Injecté pour détecter l'intention
    
    def _handle_first_message(self, message: str):
        procedure_id = self.kb_loader.detect_intent(message)
        # → "sarl_au" ou "cnss" ou "unknown"
```

**Pourquoi ?** La détection d'intention (keywords) n'est pas la responsabilité de l'agent. Elle appartient à la couche **Service** qui connaît le contenu de la KB.

---

### `agent/core.py` → `agent/planner.py`

```python
# agent/core.py
from agent.planner import Planner

class AgentCore:
    def __init__(self):
        self.planner = Planner(kb_loader=self.kb_loader)
    
    def _handle_first_message(self, message: str):
        self.planner.create_plan(procedure_id)  # → charge plan depuis KB
```

```python
# agent/planner.py
class Planner:
    def create_plan(self, procedure_id: str):
        self.procedure = self.kb_loader.load_procedure(procedure_id)
        # → lit data/kb/sarl_au.json
        # → génère la liste d'étapes avec statuts
```

**Pourquoi ?** Le `Planner` est l'orchestrateur. Il doit savoir où trouver les données (KB) mais ne doit pas savoir comment les charger. C'est pourquoi on lui injecte `KBLoader`.

---

### `agent/planner.py` → `data/kb/*.json`

```python
# agent/planner.py
def create_plan(self, procedure_id: str):
    self.procedure = self.kb_loader.load_procedure(procedure_id)
    # KBLoader lit le fichier JSON correspondant
```

```python
# services/kb_loader.py
def load_procedure(self, procedure_id: str) -> dict:
    path = self.kb_dir / f"{procedure_id}.json"
    # → data/kb/sarl_au.json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
```

**Pourquoi JSON ?**
- **Lisible par humain** — peut être modifié sans code
- **Versionnable** — git diff montre les changements
- **No SQL** — pas besoin d'une base pour le contenu statique

---

### `agent/core.py` → `agent/context.py`

```python
# agent/core.py
from agent.context import ContextManager

class AgentCore:
    def __init__(self):
        self.context = ContextManager()
    
    def respond(self, user_message: str):
        self.context.add_message("user", user_message)
        # ...
        self.context.add_message("assistant", response)
```

```python
# agent/context.py
class ContextManager:
    def get_history_for_llm(self) -> list:
        return [{"role": msg["role"], "content": msg["content"]} ...]
```

**Pourquoi ?** Streamlit ré-exécute tout le script à chaque interaction. Sans `ContextManager` (stocké dans `st.session_state`), l'agent oublierait tout à chaque message.

---

### `agent/core.py` → `services/llm.py`

```python
# agent/core.py
from services.llm import LLMService

class AgentCore:
    def __init__(self):
        self.llm = LLMService()  # Charge modèle depuis .env
    
    def _handle_first_message(self, message: str):
        response = self.llm.chat(
            messages=self.context.get_history_for_llm(),
            system_prompt="Tu es MAA..."
        )
```

```python
# services/llm.py
class LLMService:
    def __init__(self):
        # Lit LLM_PROVIDER et LLM_MODEL depuis .env
        if provider == "ollama":
            self.client = OpenAI(
                api_key="ollama",
                base_url="http://localhost:11434/v1",
            )
```

**Pourquoi Ollama ?**
- **Gratuit** — pas de facture API
- **Offline** — fonctionne sans internet (idéal démo jury)
- **Zéro quota** — pas de risque d'épuisement

---

### `app.py` → `data/db.py`

```python
# app.py
from data.db import init_db

init_db()  # Au démarrage de l'app
# → Crée data/sessions.db avec 4 tables
```

**Pourquoi SQLite ?**
- **Sans serveur** — fichier unique, facile à transporter
- **Idéal démo** — pas besoin de Docker/PostgreSQL
- **Portable** — fonctionne partout

**Pourquoi les 4 tables ?**
| Table | Usage |
|---|---|
| `sessions` | Une session par conversation utilisateur |
| `messages` | Historique complet user/assistant |
| `collected_info` | Toutes les infos récoltées (nom, CIN, etc.) |
| `steps_progress` | État de chaque étape (pending/done/blocked) |

---

## 3. Pourquoi cette architecture ?

### Pourquoi 5 couches (L1 à L5) ?

```
L1 — Presentation  →  Streamlit UI (affichage uniquement)
L2 — Agent         →  Logique métier (ReAct, planification)
L3 — Service       →  Services réutilisables (LLM, KB, RAG)
L4 — Knowledge     →  Données métier (procédures JSON)
L5 — Data          →  Persistance (SQLite)
```

**Raisons :**
1. **Séparation des responsabilités** — chaque couche a un rôle unique
2. **Testabilité** — on peut tester L2 sans L1, L3 sans L2
3. **Extensibilité** — ajouter une nouvelle procédure = juste un JSON, pas de code
4. **Compréhension jury** — architecture claire et explicable

---

### Pourquoi le pattern ReAct ?

```
ReAct = Reasoning + Acting
```

**Flux :**
1. **Reasoning** — Le LLM réfléchit (system prompt avec contexte)
2. **Acting** — L'agent exécute (appelle `planner.record_info()`)
3. **Observation** — Le système observe le résultat (`planner.missing_info()`)
4. **Répétition** — Boucle jusqu'à completion

**Pourquoi pas un simple chatbot ?**
| Chatbot classique | Agent MAA (ReAct) |
|---|---|
| Répond au coup par coup | Suit un plan structuré |
| Oublie le contexte | Maintient l'état entre messages |
| Réponses génériques | Adapte selon infos collectées |
| Pas de progression visible | Barre de progression 0–100% |

---

### Pourquoi KB-driven Planner ?

**Ancien design (hardcodé) :**
```python
PLANS = {
    "sarl_au": [
        {"id": 1, "titre": "Profil", ...},  # Hardcodé
    ]
}
```

**Nouveau design (KB-driven) :**
```python
def create_plan(self, procedure_id: str):
    self.procedure = self.kb_loader.load_procedure(procedure_id)
    # → Charge depuis data/kb/sarl_au.json
```

**Avantages :**
- Ajouter une procédure = **2 heures** (un fichier JSON) au lieu de **2 jours** (code)
- Non-techniciens peuvent modifier les procédures
- Git diff montre clairement les changements métier
- Le code ne change jamais quand la procédure change

---

### Pourquoi Streamlit et pas React/Vue ?

**Streamlit :**
- **Zéro HTML/CSS** — tout en Python
- **1 commande** pour lancer (`streamlit run app.py`)
- **Chat natif** — `st.chat_message()`, `st.chat_input()`
- **Idéal démo** — impressionne le jury en 5 min

**React/Vue :**
- Nécessite frontend + backend
- Beaucoup plus de code
- Temps de développement plus long

---

## 4. Résumé du "pourquoi" de chaque fichier

| Fichier | Rôle | Pourquoi |
|---|---|---|
| `data/kb/*.json` | Contenu métier | Modifiable sans code, versionnable |
| `services/kb_loader.py` | Service de chargement | Abstraction sur les fichiers JSON |
| `agent/planner.py` | Orchestrateur | Suit le plan, gère les états |
| `agent/context.py` | Mémoire de session | Survit aux re-runs Streamlit |
| `agent/core.py` | Cerveau | Boucle ReAct, coordonne tout |
| `services/llm.py` | Service LLM | Abstraction sur Ollama/OpenRouter |
| `data/db.py` | Persistance | Stocke sessions et infos |
| `app.py` | UI | Affichage uniquement, pas de logique |
| `tests/test_planner.py` | Tests unitaires | Garantie de qualité |

---

## 5. Ce qui n'est PAS implémenté encore (Jour 5-7)

| Composant | Fichier | Jour |
|---|---|---|
| RAG / ChromaDB | `services/rag.py` | Jour 5 |
| Génération PDF | `tools/doc_gen.py` | Jour 6 |
| MLflow tracking | — | Jour 7 |
| Support arabe | — | Jour 6 |

**Pourquoi plus tard ?**
- Jour 1-2 = **MVP fonctionnel** (KB + Agent + UI)
- Jour 3-4 = **Polish** (multi-sessions, export)
- Jour 5-7 = **Features avancées** (RAG, PDF, MLflow)

C'est le principe du **"working software over comprehensive documentation"** du manifeste Agile — livrer du qui marche d'abord, améliorer ensuite.

---

## 6. Tests et validation

### Tests unitaires (`tests/test_planner.py`)

25 tests couvrent :
- KBLoader : chargement des 5 procédures, détection d'intention
- Planner : création de plan, progression, completion
- Tous les tests passent ✅

### Test CLI (`test_agent.py`)

Script de test manuel qui valide :
- KBLoader charge les 5 procédures
- Planner crée le plan correctement
- SQLite initialise les 4 tables
- Agent conversation avec Ollama (nécessite `ollama serve`)

### Lancement des tests

```powershell
uv run pytest tests/test_planner.py -v
uv run python test_agent.py
```

---

## 7. Livrables Jour 1

### Fichiers créés
- `data/kb/sarl_au.json` — 5 étapes, 2520 MAD frais
- `data/kb/cnss.json` — 4 étapes, 0 MAD frais
- `data/kb/ompic.json` — 5 étapes, 650 MAD frais
- `data/kb/dgi.json` — 4 étapes, 0 MAD frais
- `data/kb/rc.json` — 4 étapes, 350 MAD frais
- `services/kb_loader.py` — KBLoader complet
- `agent/context.py` — ContextManager
- `agent/planner.py` — Planner KB-driven
- `agent/core.py` — AgentCore ReAct
- `data/db.py` — SQLite 4 tables
- `app.py` — Streamlit UI
- `tests/test_planner.py` — 25 tests unitaires

### Fichiers modifiés
- `services/llm.py` — Nettoyage (suppression garbage)
- `.gitignore` — Ajout fichiers non-source
- `.env.example` — Template configuration
- `README.md` — Documentation complète

---

## 8. Commandes utiles

```powershell
# Lancer Ollama (terminal dédié)
ollama serve

# Lancer l'app
uv run streamlit run app.py

# Tests
uv run pytest tests/ -v
uv run python test_agent.py
```

---

*Fin de la documentation Jour 1*
