from agent.context import ContextManager
from agent.planner import Planner
from services.kb_loader import KBLoader
from services.llm import LLMService


class AgentCore:

    def __init__(self):
        self.kb_loader: KBLoader        = KBLoader()
        self.planner:   Planner         = Planner(kb_loader=self.kb_loader)
        self.context:   ContextManager  = ContextManager()
        self.llm:       LLMService      = LLMService()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def respond(self, user_message: str) -> str:
        self.context.add_message("user", user_message)

        if not self.planner.plan:
            response = self._handle_first_message(user_message)
        elif not self.planner.is_complete():
            response = self._handle_collection(user_message)
        else:
            response = self._handle_completion()

        self.context.add_message("assistant", response)
        return response

    # ------------------------------------------------------------------
    # Phase handlers
    # ------------------------------------------------------------------

    def _handle_first_message(self, message: str) -> str:
        procedure_id = self.kb_loader.detect_intent(message)

        if procedure_id == "unknown":
            procedures = self.kb_loader.list_procedures()
            proc_list  = "\n".join(
                f"- {p['id']}: {p['titre']}" for p in procedures
            )
            return self.llm.chat(
                messages=self.context.get_history_for_llm(),
                system_prompt=(
                    "Tu es MAA, assistant administratif marocain expert. "
                    "L'utilisateur n'a pas précisé sa démarche. "
                    f"Voici les procédures disponibles :\n{proc_list}\n"
                    "Demande-lui poliment quelle démarche il souhaite effectuer. "
                    "Réponds en français."
                ),
            )

        self.planner.create_plan(procedure_id)
        self.context.procedure_id = procedure_id
        summary     = self.kb_loader.get_procedure_summary(procedure_id)
        first_label = self.planner.missing_info_label()

        system = (
            "Tu es MAA, assistant administratif marocain expert. "
            f"L'utilisateur veut : {message}.\n"
            f"Résumé de la procédure :\n{summary}\n"
            f"Plan :\n{self.planner.plan_summary()}\n"
            f"Annonce brièvement le plan et pose la première question : "
            f"'{first_label}'. Sois précis, chaleureux et professionnel. "
            "Réponds en français."
        )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    def _handle_collection(self, message: str) -> str:
        missing_key = self.planner.missing_info()
        if missing_key:
            self.planner.record_info(missing_key, message)
            self.context.update_info(missing_key, message)

        if self.planner.is_complete():
            return self._handle_completion()

        next_label   = self.planner.missing_info_label()
        current_step = self.planner.current_step()
        docs         = ", ".join(current_step.get("docs_requis", [])) or "aucun"

        system = (
            "Tu es MAA, assistant administratif marocain expert. "
            f"Étape en cours : '{current_step['titre']}' [{current_step['organisme']}].\n"
            f"Documents requis pour cette étape : {docs}.\n"
            f"Infos déjà collectées : {self.context.get_collected_info()}.\n"
            f"Pose maintenant la question suivante : '{next_label}'.\n"
            "Sois concis et professionnel. Réponds en français."
        )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    def _handle_completion(self) -> str:
        proc       = self.planner.procedure
        total_fees = self.planner.get_total_fees()

        system = (
            "Tu es MAA, assistant administratif marocain expert. "
            f"Toutes les informations ont été collectées pour : {proc.get('titre', '')}.\n"
            f"Résumé des infos : {self.context.get_collected_info()}.\n"
            f"Plan complet :\n{self.planner.plan_summary()}\n"
            f"Frais totaux estimés : {total_fees} MAD\n"
            f"Durée estimée : {proc.get('duree_est', '—')}\n"
            "Félicite l'utilisateur, résume les informations collectées, "
            "et donne les prochaines étapes concrètes à suivre avec les documents "
            "à préparer. Réponds en français."
        )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        self.planner = Planner(kb_loader=self.kb_loader)
        self.context = ContextManager()
