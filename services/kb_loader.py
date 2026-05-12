import json
from pathlib import Path

KB_DIR = Path(__file__).parent.parent / "data" / "kb"

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "sarl_au": [
        "sarl au", "sarl à associé unique", "sarl a associé",
        "créer une sarl", "créer ma société", "créer ma sarl",
        "ouvrir une société", "monter une société",
    ],
    "cnss": [
        "cnss", "sécurité sociale", "immatricul", "cotisation",
        "employeur cnss", "affilier", "affiliation cnss",
    ],
    "ompic": [
        "ompic", "marque", "dépôt de marque", "certificat négatif",
        "déposer une marque", "protéger ma marque", "enregistrer une marque",
    ],
    "dgi": [
        "dgi", "identifiant fiscal", "impôts", "if fiscal",
        "inscription fiscale", "taxe", "tva",
    ],
    "rc": [
        "registre de commerce", " rc ", "immatriculation rc",
        "tribunal de commerce", "extrait rc", "numéro rc",
    ],
    "recommandation": [
        "créer une entreprise", "créer mon entreprise", "lancer une entreprise",
        "monter un business", "monter mon business", "créer une startup",
        "quelle forme juridique", "quel statut juridique", "quelle structure",
        "je ne sais pas quel type", "conseille moi", "recommande moi",
        "aide moi à choisir", "quel est le meilleur statut", "quel statut choisir",
        "auto entrepreneur ou sarl", "sarl ou auto", "quelle société",
    ],
}


class KBLoader:

    def __init__(self, kb_dir: str | None = None):
        self.kb_dir = Path(kb_dir) if kb_dir else KB_DIR

    def load_procedure(self, procedure_id: str) -> dict:
        path = self.kb_dir / f"{procedure_id}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Procédure '{procedure_id}' introuvable dans {self.kb_dir}"
            )
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_procedures(self) -> list[dict]:
        procedures = []
        for path in sorted(self.kb_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                procedures.append({
                    "id":          data["id"],
                    "titre":       data["titre"],
                    "description": data.get("description", ""),
                    "duree_est":   data.get("duree_est", "—"),
                    "frais_est":   data.get("frais_est", {}),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return procedures

    def get_procedure_summary(self, procedure_id: str) -> str:
        proc = self.load_procedure(procedure_id)
        etapes = proc.get("etapes", [])
        frais = proc.get("frais_est", {})
        lines = [
            f"Procédure : {proc['titre']}",
            f"Organismes : {', '.join(proc.get('organisme', []))}",
            f"Durée estimée : {proc.get('duree_est', '—')}",
            f"Frais estimés : {frais.get('min', 0)}–{frais.get('max', 0)} MAD",
            f"Nombre d'étapes : {len(etapes)}",
            "Étapes :",
        ]
        for e in etapes:
            lines.append(
                f"  {e['id']}. {e['titre']} [{e['organisme']}]"
                f" — {e.get('delai', '—')} — {e.get('frais', 0)} MAD"
            )
        return "\n".join(lines)

    def detect_intent(self, message: str) -> str:
        msg = " " + message.lower() + " "
        for proc_id, keywords in _INTENT_KEYWORDS.items():
            if any(kw in msg for kw in keywords):
                return proc_id
        return "unknown"
