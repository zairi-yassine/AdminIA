LEGAL_STATUS_INFO: dict[str, dict] = {
    "auto_entrepreneur": {
        "nom": "Auto-Entrepreneur",
        "description": (
            "Statut simplifié pour les activités individuelles de service "
            "ou d'artisanat avec chiffre d'affaires limité."
        ),
        "avantages": [
            "Création en 24h via le portail en ligne (auto-entrepreneur.ma)",
            "Comptabilité ultra-simplifiée (pas de bilan obligatoire)",
            "Cotisations proportionnelles au CA réel",
            "Zéro charge si pas de chiffre d'affaires",
            "Pas de capital minimum requis",
        ],
        "inconvenients": [
            "Plafond CA : 500 000 MAD/an (services) ou 2 000 000 MAD/an (commerce)",
            "Responsabilité illimitée sur le patrimoine personnel",
            "Impossible de récupérer la TVA",
            "Difficile d'embaucher des salariés",
        ],
        "ideal_pour": "Freelances, consultants, artisans solo avec faible CA",
        "lien_officiel": "https://auto-entrepreneur.ma",
        "procedure_maa": None,
    },
    "sarl_au": {
        "nom": "SARL à Associé Unique (SARL AU)",
        "description": (
            "Société à responsabilité limitée avec un seul associé fondateur. "
            "La forme juridique la plus populaire au Maroc pour les entrepreneurs solo."
        ),
        "avantages": [
            "Capital minimum symbolique : 1 MAD légalement",
            "Responsabilité limitée à l'apport (patrimoine personnel protégé)",
            "Forte crédibilité bancaire et commerciale",
            "IS réduit à 10% pour bénéfice net < 300 000 MAD/an",
            "Facilement transformable en SARL multi-associés",
        ],
        "inconvenients": [
            "Frais de création : 3 000 à 5 000 MAD",
            "Comptabilité certifiée obligatoire",
            "Durée de création : 2 à 4 semaines",
            "Assemblée générale annuelle obligatoire",
        ],
        "ideal_pour": "Entrepreneur solo avec CA > 500K MAD ou besoin de crédibilité B2B",
        "lien_officiel": "https://www.registrecommerce.ma",
        "procedure_maa": "sarl_au",
    },
    "sarl": {
        "nom": "SARL (2 à 50 associés)",
        "description": (
            "Société à responsabilité limitée avec plusieurs associés. "
            "Idéale pour les projets d'équipe."
        ),
        "avantages": [
            "Responsabilité limitée à l'apport pour tous les associés",
            "Flexibilité dans la répartition des parts sociales",
            "Capital minimum : 1 MAD",
            "Structure adaptée aux projets multi-fondateurs",
        ],
        "inconvenients": [
            "Nécessite un accord formel entre associés (pacte recommandé)",
            "Gestion plus complexe qu'une SARL AU",
            "Risque de conflits entre associés",
        ],
        "ideal_pour": "2 à 50 associés avec parts et responsabilités à répartir",
        "lien_officiel": "https://www.registrecommerce.ma",
        "procedure_maa": None,
    },
    "sa": {
        "nom": "Société Anonyme (SA)",
        "description": (
            "Société par actions pour les grands projets capitalistiques. "
            "Structure adaptée aux levées de fonds importantes."
        ),
        "avantages": [
            "Peut faire appel public à l'épargne (Bourse)",
            "Structure optimale pour lever des fonds importants",
            "Crédibilité maximale (banques, investisseurs, partenaires)",
            "Peut avoir un nombre illimité d'actionnaires",
        ],
        "inconvenients": [
            "Capital minimum obligatoire : 300 000 MAD",
            "5 actionnaires minimum",
            "Gouvernance lourde (Conseil d'Administration, DG, Commissaire aux Comptes)",
            "Coûts de fonctionnement élevés",
        ],
        "ideal_pour": "Grands projets, capital > 300K MAD, 5+ actionnaires, ambition Bourse",
        "lien_officiel": "https://www.registrecommerce.ma",
        "procedure_maa": None,
    },
}

_PROFILE_QUESTIONS: list[dict] = [
    {
        "key":   "nb_associes",
        "label": (
            "Combien de personnes vont fonder cette entreprise ? "
            "(répondez par un chiffre : 1, 2, 5…)"
        ),
    },
    {
        "key":   "ca_previsionnel",
        "label": (
            "Quel est votre chiffre d'affaires annuel prévisionnel en MAD ? "
            "(ex: 200000 pour 200 000 MAD)"
        ),
    },
    {
        "key":   "type_activite",
        "label": (
            "Quel est le type d'activité principal ? "
            "(service / commerce / artisanat / industrie)"
        ),
    },
    {
        "key":   "capital_disponible",
        "label": (
            "Quel montant de capital pouvez-vous investir au départ en MAD ? "
            "(ex: 10000 pour 10 000 MAD)"
        ),
    },
]


class Recommender:

    def __init__(self):
        self.collected: dict[str, str] = {}
        self.result:    dict | None    = None

    # ------------------------------------------------------------------
    # Question flow
    # ------------------------------------------------------------------

    def get_next_question(self) -> tuple[str, str] | None:
        for q in _PROFILE_QUESTIONS:
            if q["key"] not in self.collected:
                return q["key"], q["label"]
        return None

    def record(self, key: str, value: str):
        self.collected[key] = value.strip()

    def is_profile_complete(self) -> bool:
        return all(q["key"] in self.collected for q in _PROFILE_QUESTIONS)

    # ------------------------------------------------------------------
    # Decision tree
    # ------------------------------------------------------------------

    def analyze(self) -> dict:
        nb      = self._parse_int(self.collected.get("nb_associes",      "1"))
        ca      = self._parse_float(self.collected.get("ca_previsionnel",  "0"))
        capital = self._parse_float(self.collected.get("capital_disponible", "0"))
        activite = self.collected.get("type_activite", "service").lower()

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

        self.result = {
            "status_id":    status_id,
            "status_info":  LEGAL_STATUS_INFO[status_id],
            "procedure_id": LEGAL_STATUS_INFO[status_id]["procedure_maa"],
            "profile":      dict(self.collected),
        }
        return self.result

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_recommendation(self) -> str:
        if not self.result:
            self.analyze()
        info = self.result["status_info"]
        lines = [
            f"Statut recommandé : {info['nom']}",
            f"",
            f"{info['description']}",
            f"",
            f"Avantages :",
        ]
        for av in info["avantages"]:
            lines.append(f"  + {av}")
        lines += ["", "Points à noter :"]
        for inc in info["inconvenients"]:
            lines.append(f"  - {inc}")
        lines += [
            "",
            f"Idéal pour : {info['ideal_pour']}",
            f"Lien officiel : {info['lien_officiel']}",
        ]
        if self.result["procedure_id"]:
            lines.append(
                "\nMAA peut vous guider pas-à-pas dans cette procédure. "
                "Souhaitez-vous commencer ?"
            )
        else:
            lines.append(
                "\nCe statut sera disponible dans une prochaine version de MAA. "
                "En attendant, consultez le lien officiel ci-dessus."
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_int(value: str) -> int:
        try:
            return int("".join(c for c in str(value) if c.isdigit()) or "1")
        except ValueError:
            return 1

    @staticmethod
    def _parse_float(value: str) -> float:
        try:
            cleaned = "".join(c for c in str(value) if c.isdigit() or c == ".")
            return float(cleaned or "0")
        except ValueError:
            return 0.0

    def reset(self):
        self.__init__()
