from agent.context import ContextManager
from agent.planner import Planner
from services.kb_loader import KBLoader
from services.llm import LLMService
from services.recommender import Recommender
from services.rag import RAGService
from services.session_manager import SessionManager

_POSITIVE_WORDS = {"oui", "yes", "ok", "d'accord", "allons-y", "commence",
                   "démarrer", "démarrons", "go", "parfait", "super", "bien sûr"}


class AgentCore:

    def __init__(self):
        self.kb_loader:          KBLoader        = KBLoader()
        self.planner:            Planner         = Planner(kb_loader=self.kb_loader)
        self.context:            ContextManager  = ContextManager()
        self.llm:                LLMService      = LLMService()
        self.recommender:        Recommender     = Recommender()
        self.session_mgr:        SessionManager  = SessionManager()
        self.session_id:         str | None      = None
        self._in_recommendation: bool            = False
        self._pending_procedure: str | None      = None
        self.rag:                RAGService      = RAGService()
        try:
            self.rag.index_kb(self.kb_loader)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def respond(self, user_message: str) -> str:
        if not self.session_id:
            self.session_id = self.session_mgr.create_session()

        self.context.add_message("user", user_message)
        self.session_mgr.save_message(self.session_id, "user", user_message)

        if self._in_recommendation:
            response = self._handle_recommendation_collection(user_message)
        elif self._pending_procedure:
            response = self._handle_procedure_confirmation(user_message)
        elif not self.planner.plan:
            response = self._handle_first_message(user_message)
        elif not self.planner.is_complete():
            response = self._handle_collection(user_message)
        else:
            response = self._handle_completion()

        self.context.add_message("assistant", response)
        self.session_mgr.save_message(self.session_id, "assistant", response)

        if self.context.procedure_id:
            self.session_mgr.update_session(
                self.session_id, procedure_id=self.context.procedure_id
            )
        if self.planner.plan:
            self._sync_steps_to_db()

        return response

    # ------------------------------------------------------------------
    # Phase 0 — Routing
    # ------------------------------------------------------------------

    def _handle_first_message(self, message: str) -> str:
        procedure_id = self.kb_loader.detect_intent(message)

        if procedure_id == "recommandation":
            self._in_recommendation = True
            _, first_label = self.recommender.get_next_question()
            system = (
                "Tu es MAA, assistant administratif marocain expert. "
                "L'utilisateur veut créer une entreprise mais n'a pas précisé la forme juridique. "
                "Tu vas lui poser 4 courtes questions pour lui recommander le statut optimal "
                "(Auto-entrepreneur, SARL AU, SARL ou SA). "
                f"Explique-lui brièvement l'objectif, puis pose la première question : "
                f"'{first_label}'. Sois chaleureux et professionnel. Réponds en français."
            )
            return self.llm.chat(self.context.get_history_for_llm(), system)

        if procedure_id == "unknown":
            procedures = self.kb_loader.list_procedures()
            proc_list  = "\n".join(
                f"- {p['titre']}" for p in procedures
            )
            return self.llm.chat(
                messages=self.context.get_history_for_llm(),
                system_prompt=(
                    "Tu es MAA, assistant administratif marocain expert. "
                    "L'utilisateur n'a pas précisé sa démarche. "
                    f"Procédures disponibles :\n{proc_list}\n"
                    "Tu peux aussi l'aider à choisir sa forme juridique "
                    "(Auto-entrepreneur, SARL AU, SARL, SA) s'il ne sait pas encore. "
                    "Demande-lui poliment ce qu'il souhaite faire. Réponds en français."
                ),
            )

        self.planner.create_plan(procedure_id)
        self.context.procedure_id = procedure_id
        summary     = self.kb_loader.get_procedure_summary(procedure_id)
        first_label = self.planner.missing_info_label()
        rag_context = self.rag.query(message, n_results=2, procedure_id=procedure_id)
        system = (
            "Tu es MAA, assistant administratif marocain expert. "
            f"L'utilisateur veut : {message}.\n"
            f"Résumé de la procédure :\n{summary}\n"
            f"Plan :\n{self.planner.plan_summary()}\n"
            + (f"Documentation officielle :\n{rag_context}\n" if rag_context else "")
            + f"Annonce brièvement le plan et pose la première question : "
            f"'{first_label}'. Sois précis, chaleureux et professionnel. "
            "Réponds en français."
        )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    # ------------------------------------------------------------------
    # Phase 1 — Smart Recommendations (collecte profil)
    # ------------------------------------------------------------------

    def _handle_recommendation_collection(self, message: str) -> str:
        next_q = self.recommender.get_next_question()
        if next_q:
            key, _ = next_q
            self.recommender.record(key, message)

        if self.recommender.is_profile_complete():
            self._in_recommendation = False
            result   = self.recommender.analyze()
            rec_text = self.recommender.format_recommendation()

            if result["procedure_id"]:
                self._pending_procedure = result["procedure_id"]
                system = (
                    "Tu es MAA, assistant administratif marocain expert. "
                    f"Voici l'analyse du profil utilisateur :\n{rec_text}\n"
                    "Présente cette recommandation de manière claire et enthousiaste. "
                    "Explique en 2-3 phrases pourquoi c'est le meilleur choix pour son profil. "
                    "Dis-lui que MAA peut le guider dans toute la procédure "
                    "et demande-lui s'il veut commencer maintenant. Réponds en français."
                )
            else:
                system = (
                    "Tu es MAA, assistant administratif marocain expert. "
                    f"Voici l'analyse du profil utilisateur :\n{rec_text}\n"
                    "Présente cette recommandation clairement. "
                    "Informe l'utilisateur que MAA ne couvre pas encore ce statut "
                    "mais l'orientera vers les ressources officielles. "
                    "Propose-lui de l'aider pour une autre démarche. Réponds en français."
                )
            return self.llm.chat(self.context.get_history_for_llm(), system)

        next_q = self.recommender.get_next_question()
        if next_q:
            _, label = next_q
            system = (
                "Tu es MAA. Tu collectes le profil pour recommander la meilleure forme juridique. "
                f"Pose la question suivante de manière naturelle : '{label}'. "
                "Sois bref et encourageant. Réponds en français."
            )
            return self.llm.chat(self.context.get_history_for_llm(), system)

        return "Analyse en cours…"

    # ------------------------------------------------------------------
    # Phase 2 — Confirmation de procédure post-recommandation
    # ------------------------------------------------------------------

    def _handle_procedure_confirmation(self, message: str) -> str:
        msg_words = set(message.lower().split())
        confirmed = bool(msg_words & _POSITIVE_WORDS)

        if confirmed:
            procedure_id            = self._pending_procedure
            self._pending_procedure = None
            self.planner.create_plan(procedure_id)
            self.context.procedure_id = procedure_id
            summary     = self.kb_loader.get_procedure_summary(procedure_id)
            first_label = self.planner.missing_info_label()
            system = (
                "Tu es MAA, assistant administratif marocain expert. "
                "L'utilisateur confirme vouloir démarrer la procédure.\n"
                f"Résumé :\n{summary}\n"
                f"Plan :\n{self.planner.plan_summary()}\n"
                f"Annonce le plan et pose la première question : '{first_label}'. "
                "Sois enthousiaste et professionnel. Réponds en français."
            )
        else:
            self._pending_procedure = None
            system = (
                "Tu es MAA. L'utilisateur ne souhaite pas démarrer la procédure maintenant. "
                "Remercie-le et demande-lui si tu peux l'aider autrement. Réponds en français."
            )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    def _sync_steps_to_db(self):
        if not self.session_id:
            return
        for step in self.planner.plan:
            self.session_mgr.upsert_step_progress(
                self.session_id,
                step["id"],
                step["titre"],
                step["statut"].value,
            )

    # ------------------------------------------------------------------
    # Phase 3 — Collecte d'informations (procédure en cours)
    # ------------------------------------------------------------------

    def _handle_collection(self, message: str) -> str:
        missing_key  = self.planner.missing_info()
        current_step = self.planner.current_step()
        if missing_key:
            self.planner.record_info(missing_key, message)
            self.context.update_info(missing_key, message)
            if self.session_id and current_step:
                self.session_mgr.save_collected_info(
                    self.session_id,
                    current_step["id"],
                    missing_key,
                    message,
                )

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

    # ------------------------------------------------------------------
    # Phase 4 — Finalisation
    # ------------------------------------------------------------------

    def _handle_completion(self) -> str:
        proc       = self.planner.procedure
        total_fees = self.planner.get_total_fees()
        rag_context = self.rag.query(
            f"etapes documents frais {proc.get('titre', '')}",
            n_results=3,
            procedure_id=self.context.procedure_id,
        )
        system = (
            "Tu es MAA, assistant administratif marocain expert. "
            f"Toutes les informations ont été collectées pour : {proc.get('titre', '')}.\n"
            f"Résumé des infos : {self.context.get_collected_info()}.\n"
            f"Plan complet :\n{self.planner.plan_summary()}\n"
            f"Frais totaux estimés : {total_fees} MAD\n"
            f"Durée estimée : {proc.get('duree_est', '-')}\n"
            + (f"Documentation officielle :\n{rag_context}\n" if rag_context else "")
            + "Félicite l'utilisateur, résume les informations collectées, "
            "et donne les prochaines étapes concrètes avec les documents à préparer. "
            "Réponds en français."
        )
        return self.llm.chat(self.context.get_history_for_llm(), system)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        if self.session_id:
            self.session_mgr.close_session(self.session_id)
        self.planner             = Planner(kb_loader=self.kb_loader)
        self.context             = ContextManager()
        self.recommender         = Recommender()
        self._in_recommendation  = False
        self._pending_procedure  = None
        self.session_id          = None
