from datetime import datetime

import streamlit as st
from agent.core import AgentCore
from data.db import init_db

st.set_page_config(
    page_title="MAA — Morocco Administrative Agent",
    page_icon="🇲🇦",
    layout="wide",
)

init_db()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = AgentCore()

agent: AgentCore = st.session_state.agent

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇲🇦 MAA")
    st.caption("Morocco Administrative Agent")
    st.divider()

    # ── Progression ────────────────────────────────────────────────────
    progress    = agent.planner.progress()
    total_steps = len(agent.planner.plan)
    done_steps  = int(progress * total_steps) if total_steps else 0

    st.markdown("**📊 Progression**")
    st.progress(progress)
    if total_steps:
        st.caption(f"{done_steps} / {total_steps} étape(s) complétée(s)")
    else:
        st.caption("En attente de votre demande…")

    # ── Plan en cours ──────────────────────────────────────────────────
    if agent.planner.plan:
        st.divider()
        proc_title = agent.planner.procedure.get("titre", "")
        st.markdown(f"**📋 {proc_title}**")
        icons = {
            "in_progress": "▶️",
            "done":        "✅",
            "pending":     "⏳",
            "blocked":     "❌",
        }
        for step in agent.planner.plan:
            icon = icons.get(step["statut"].value, "❓")
            st.caption(f"{icon} {step['id']}. {step['titre']}")

    # ── Infos collectées ───────────────────────────────────────────────
    if agent.context.collected_info:
        st.divider()
        st.markdown("**📝 Infos collectées**")
        for key, val in agent.context.collected_info.items():
            label = key.replace("_", " ").title()
            st.caption(f"• **{label}** : {val}")

    # ── Session courante ───────────────────────────────────────────────
    if agent.session_id:
        st.divider()
        short_id = agent.session_id[:8]
        st.caption(f"🔑 Session : `{short_id}…`")

    # ── Sessions récentes ──────────────────────────────────────────────
    st.divider()
    st.markdown("**🕑 Sessions récentes**")
    try:
        sessions = agent.session_mgr.list_sessions(limit=5)
        if sessions:
            for s in sessions:
                proc   = s.get("procedure_id") or "—"
                msgs   = s.get("nb_messages", 0)
                date   = s.get("created_at", "")[:10]
                status = "✅" if s.get("status") == "closed" else "🟢"
                st.caption(f"{status} {date} · **{proc}** · {msgs} msgs")
        else:
            st.caption("Aucune session enregistrée")
    except Exception:
        st.caption("—")

    # ── Procédures disponibles ─────────────────────────────────────────
    st.divider()
    st.markdown("**🗂️ Procédures disponibles**")
    try:
        from services.kb_loader import KBLoader
        for proc in KBLoader().list_procedures():
            st.caption(f"� {proc['titre']}")
    except Exception:
        pass

    # ── Nouvelle conversation ──────────────────────────────────────────
    st.divider()
    if st.button("🔄 Nouvelle conversation", use_container_width=True):
        agent.reset()
        st.session_state.messages = []
        st.rerun()

# ── Main area ──────────────────────────────────────────────────────────
st.title("🇲🇦 MAA — Morocco Administrative Agent")
st.caption("Assistant intelligent pour vos démarches administratives au Maroc")

# ── Completion banner + PDF ────────────────────────────────────────────
if agent.planner.is_complete():
    st.success(
        "✅ Toutes les informations ont été collectées ! "
        "Téléchargez votre résumé PDF ci-dessous."
    )
    try:
        from tools.doc_gen import PDFGenerator
        pdf_bytes = PDFGenerator().generate_summary(
            procedure      = agent.planner.procedure,
            collected_info = agent.context.collected_info,
            plan           = agent.planner.plan,
            session_id     = agent.session_id or "",
        )
        filename = (
            f"MAA_{agent.context.procedure_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        st.download_button(
            label             = "📥 Télécharger le résumé PDF",
            data              = pdf_bytes,
            file_name         = filename,
            mime              = "application/pdf",
            use_container_width = True,
        )
    except Exception as exc:
        st.warning(f"PDF non disponible : {exc}")
    st.divider()

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Bonjour ! Je suis **MAA**, votre assistant pour les démarches "
            "administratives au Maroc. 🇲🇦\n\n"
            "Je peux vous aider à :\n"
            "- 🏢 Créer une **SARL à Associé Unique (SARL AU)**\n"
            "- 🛡️ S'immatriculer à la **CNSS** (employeur)\n"
            "- ™️ Déposer une **marque à l'OMPIC**\n"
            "- 🧾 Obtenir un **Identifiant Fiscal (DGI)**\n"
            "- 📋 S'inscrire au **Registre de Commerce (RC)**\n\n"
            "💡 Si vous ne savez pas quel statut choisir, dites-moi simplement "
            "**« je veux créer une entreprise »** et je vous guiderai.\n\n"
            "**Quelle démarche souhaitez-vous effectuer aujourd'hui ?**"
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Décrivez votre démarche administrative…")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("MAA réfléchit…"):
            try:
                response = agent.respond(user_input)
            except Exception as exc:
                response = (
                    "⚠️ Je ne peux pas joindre le modèle de langage. "
                    "Vérifiez qu'Ollama est lancé (`ollama serve`) "
                    f"et que le modèle est disponible.\n\nDétail : `{exc}`"
                )
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()
