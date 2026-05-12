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

    progress    = agent.planner.progress()
    total_steps = len(agent.planner.plan)
    done_steps  = int(progress * total_steps) if total_steps else 0

    st.markdown("**Progression**")
    st.progress(progress)
    if total_steps:
        st.caption(f"Étape {done_steps} / {total_steps} complétée(s)")
    else:
        st.caption("En attente de votre demande…")

    if agent.planner.plan:
        st.divider()
        st.markdown("**Plan en cours**")
        icons = {
            "in_progress": "▶️",
            "done":        "✅",
            "pending":     "⏳",
            "blocked":     "❌",
        }
        for step in agent.planner.plan:
            icon = icons.get(step["statut"].value, "❓")
            st.caption(f"{icon} {step['id']}. {step['titre']}")

    st.divider()
    st.markdown("**Procédures disponibles**")
    try:
        from services.kb_loader import KBLoader
        for proc in KBLoader().list_procedures():
            st.caption(f"📋 {proc['titre']}")
    except Exception:
        pass

    st.divider()
    if st.button("🔄 Nouvelle conversation", use_container_width=True):
        agent.reset()
        st.session_state.messages = []
        st.rerun()

# ── Main area ──────────────────────────────────────────────────────────
st.title("🇲🇦 MAA — Morocco Administrative Agent")
st.caption("Assistant intelligent pour vos démarches administratives au Maroc")

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Bonjour ! Je suis **MAA**, votre assistant pour les démarches "
            "administratives au Maroc. 🇲🇦\n\n"
            "Je peux vous guider pour :\n"
            "- 🏢 Créer une **SARL à Associé Unique (SARL AU)**\n"
            "- 🛡️ S'immatriculer à la **CNSS** (employeur)\n"
            "- ™️ Déposer une **marque à l'OMPIC**\n"
            "- 🧾 Obtenir un **Identifiant Fiscal (DGI)**\n"
            "- 📋 S'inscrire au **Registre de Commerce (RC)**\n\n"
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
            response = agent.respond(user_input)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()
