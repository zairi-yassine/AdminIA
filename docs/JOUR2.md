# Documentation Jour 2 — Smart Recommendations + Agent ReAct Complet

> **Date** : 12 Mai 2026  
> **Livrable** : Smart Recommendations (arbre de décision) + Agent multi-phases complet

---

## 1. Ce qui a été ajouté

### Nouveau fichier : `services/recommender.py`

Contient :
- `LEGAL_STATUS_INFO` — dictionnaire des 4 statuts juridiques (Auto-entrepreneur, SARL AU, SARL, SA) avec avantages, inconvénients, et lien MAA
- `Recommender` — classe qui collecte le profil utilisateur (4 questions), applique l'arbre de décision, et formate la recommandation

### Fichiers modifiés

| Fichier | Changement |
|---|---|
| `services/kb_loader.py` | Ajout de l'intent `recommandation` |
| `agent/core.py` | 2 nouvelles phases + 2 nouveaux flags |

---

## 2. Les 4 statuts juridiques couverts

| Statut | Conditions | Procédure MAA |
|---|---|---|
| **Auto-Entrepreneur** | Seul + CA < 500K MAD + service/artisanat | ❌ (KB v2) |
| **SARL AU** | Seul + CA > 500K MAD ou commerce/industrie | ✅ `sarl_au` |
| **SARL** | 2 à 50 associés | ❌ (KB v2) |
| **SA** | 5+ associés ET capital ≥ 300K MAD | ❌ (KB v2) |

---

## 3. Arbre de décision

```
Entrée : nb_associes, ca_previsionnel, type_activite, capital_disponible
                                ↓
                    nb_associes == 1 ?
                   /               \
                Oui                Non
                 ↓                  ↓
    CA < 500K et activite       nb >= 5 et capital >= 300K ?
    service/artisanat ?         /                      \
      /        \              Oui                      Non
    Oui        Non             ↓                        ↓
     ↓          ↓             SA                      SARL
  Auto-Ent.  SARL AU
```

**Code dans `recommender.py` :**
```python
def analyze(self) -> dict:
    if nb == 1:
        if ca < 500_000 and activite in ("service", "artisanat"):
            status_id = "auto_entrepreneur"
        else:
            status_id = "sarl_au"
    elif nb >= 5 and capital >= 300_000:
        status_id = "sa"
    elif nb >= 2:
        status_id = "sarl"
    else:
        status_id = "sarl_au"
```

---

## 4. Flux complet de l'agent — 4 phases

```
respond(user_message)
    │
    ├── _in_recommendation = True ?
    │       → Phase 1 : collecte profil (4 questions)
    │               ↓ profil complet
    │           analyze() → recommandation
    │               ↓
    │       _pending_procedure = "sarl_au" ?
    │
    ├── _pending_procedure != None ?
    │       → Phase 2 : confirmation utilisateur
    │           "oui" → crée plan, démarre procédure
    │           "non" → demande autre chose
    │
    ├── planner.plan vide ?
    │       → Phase 0 : routing
    │           intent = "recommandation" → Phase 1
    │           intent = "sarl_au" → procédure directe
    │           intent = "unknown"  → liste procédures
    │
    ├── planner.is_complete() = False ?
    │       → Phase 3 : collecte infos procédure
    │
    └── planner.is_complete() = True ?
            → Phase 4 : finalisation + résumé
```

---

## 5. Pourquoi ces choix ?

### Pourquoi un arbre de décision et pas seulement le LLM ?

- **Déterministe** — même profil = même recommandation (testable)
- **Explicable** — jury peut voir la logique
- **Rapide** — pas de latence LLM pour la décision
- **Fiable** — pas d'hallucination possible sur les seuils légaux (500K MAD, 300K MAD)

Le LLM est utilisé uniquement pour **présenter** la recommandation en langage naturel, pas pour la **calculer**.

### Pourquoi `_pending_procedure` et pas démarrer directement ?

Le flux recommendation → procédure nécessite une confirmation explicite. Cela :
1. **Respecte l'UX** — l'utilisateur doit valider avant de commencer
2. **Permet un refus** — il peut vouloir juste l'info sans procédure
3. **Clair pour le jury** — étape de validation visible

### Pourquoi séparer `Recommender` de `Planner` ?

- `Planner` gère l'exécution d'une procédure connue
- `Recommender` gère la découverte du bon statut juridique
- Ce sont deux responsabilités distinctes → deux classes
- Le `Recommender` ne dépend pas de la KB (décision rule-based)

---

## 6. Nouvelle structure de `agent/core.py`

```
AgentCore
├── __init__
│   ├── kb_loader       ← KBLoader
│   ├── planner         ← Planner (KB-driven)
│   ├── context         ← ContextManager
│   ├── llm             ← LLMService
│   ├── recommender     ← Recommender (NOUVEAU)
│   ├── _in_recommendation: bool (NOUVEAU)
│   └── _pending_procedure: str|None (NOUVEAU)
│
├── respond()            ← Dispatcher des 5 phases
│
├── _handle_first_message()         ← Phase 0 : routing
├── _handle_recommendation_collection()  ← Phase 1 (NOUVEAU)
├── _handle_procedure_confirmation() ← Phase 2 (NOUVEAU)
├── _handle_collection()            ← Phase 3
├── _handle_completion()            ← Phase 4
└── reset()             ← Remet tout à zéro
```

---

## 7. Nouveau intent dans `kb_loader.py`

```python
"recommandation": [
    "créer une entreprise", "créer mon entreprise",
    "lancer une entreprise", "monter un business",
    "quelle forme juridique", "quel statut juridique",
    "aide moi à choisir", "quel est le meilleur statut",
    ...
]
```

**Important** : L'intent `recommandation` est placé EN DERNIER dans le dict pour éviter les conflits avec les intents spécifiques (`sarl_au`, etc.). Python 3.7+ maintient l'ordre d'insertion — les intents spécifiques sont vérifiés en premier.

---

## 8. Tests Jour 2

### `tests/test_recommender.py` — 25 tests

Couvre :
- Collecte de profil (4 questions dans l'ordre)
- Arbre de décision (8 cas de figure)
- Mapping statut → procédure MAA
- Formatage de la recommandation
- Complétude des données `LEGAL_STATUS_INFO`
- Reset du recommender

### Lancer les tests

```powershell
uv run pytest tests/ -v
# → 50 tests au total (25 test_planner + 25 test_recommender)
```

---

## 9. Flux de conversation — exemple Jour 2

```
👤 User : "je veux créer une entreprise"
         → intent = "recommandation"
         → _in_recommendation = True

🤖 MAA  : "Pour vous recommander le meilleur statut, j'ai 4 questions.
           Combien de personnes vont fonder cette entreprise ?"

👤 User : "1"  → nb_associes = 1

🤖 MAA  : "Quel est votre CA prévisionnel en MAD ?"

👤 User : "200000"  → ca_previsionnel = 200000

🤖 MAA  : "Quel type d'activité ?"

👤 User : "service"  → type_activite = service

🤖 MAA  : "Quel capital pouvez-vous investir ?"

👤 User : "5000"  → capital_disponible = 5000
         → is_profile_complete() = True
         → analyze() → "auto_entrepreneur"
         → procedure_id = None (pas encore dans KB)

🤖 MAA  : "Je vous recommande le statut Auto-Entrepreneur.
           Avantages : création en 24h, zéro charge si pas de CA...
           Ce statut sera bientôt disponible dans MAA."
```

---

## 10. Livrables Jour 2

### Fichiers créés
- `services/recommender.py` — Recommender + LEGAL_STATUS_INFO
- `tests/test_recommender.py` — 25 tests unitaires

### Fichiers modifiés
- `services/kb_loader.py` — intent `recommandation` ajouté
- `agent/core.py` — 2 phases + 2 flags + import Recommender

### Résultats tests
- 50 tests unitaires — 100% pass

---

## 11. Commandes utiles

```powershell
# Tests complets
uv run pytest tests/ -v

# App
uv run streamlit run app.py
```

---

*Fin de la documentation Jour 2*
