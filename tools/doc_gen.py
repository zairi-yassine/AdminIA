from datetime import datetime
from fpdf import FPDF

_STATUS_LABELS = {
    "done":        "Complete",
    "in_progress": "En cours",
    "pending":     "En attente",
    "blocked":     "Bloque",
}

_GREEN = (0,   114,  54)
_GREY  = (240, 240, 240)
_DARK  = (40,   40,  40)
_LIGHT = (120, 120, 120)


class PDFGenerator:

    def generate_summary(
        self,
        procedure:      dict,
        collected_info: dict,
        plan:           list[dict],
        session_id:     str = "",
    ) -> bytes:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        self._header(pdf, procedure, session_id)
        self._meta_section(pdf, procedure, plan)

        if collected_info:
            self._collected_section(pdf, collected_info)

        self._plan_section(pdf, plan)
        self._footer(pdf)

        return bytes(pdf.output())

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _header(self, pdf: FPDF, procedure: dict, session_id: str):
        pdf.set_fill_color(*_GREEN)
        pdf.rect(0, 0, 210, 32, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_y(7)
        pdf.cell(0, 10, "MAA - Morocco Administrative Agent",
                 align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, "Resume de procedure administrative",
                 align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*_DARK)
        pdf.set_y(38)

        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, self._safe(procedure.get("titre", "Procedure")),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_LIGHT)
        pdf.cell(0, 5,
                 f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
                 new_x="LMARGIN", new_y="NEXT")
        if session_id:
            pdf.cell(0, 5, f"Session : {session_id[:8]}...",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*_DARK)
        pdf.ln(5)

    def _meta_section(self, pdf: FPDF, procedure: dict, plan: list[dict]):
        self._section_title(pdf, "Informations generales")
        organismes = ", ".join(procedure.get("organisme", [])) or "—"
        frais_est  = procedure.get("frais_est", {})
        total_fees = sum(s.get("frais", 0) for s in plan)
        self._row(pdf, "Organismes",     organismes)
        self._row(pdf, "Duree estimee",  procedure.get("duree_est", "—"))
        self._row(pdf, "Frais estimes",
                  f"{frais_est.get('min', 0)} a {frais_est.get('max', 0)} MAD")
        self._row(pdf, "Frais calcules", f"{total_fees} MAD")
        pdf.ln(5)

    def _collected_section(self, pdf: FPDF, collected_info: dict):
        self._section_title(pdf, "Informations collectees")
        for key, value in collected_info.items():
            label = key.replace("_", " ").title()
            self._row(pdf, label, str(value))
        pdf.ln(5)

    def _plan_section(self, pdf: FPDF, plan: list[dict]):
        self._section_title(pdf, "Plan des etapes")
        for step in plan:
            statut_raw = step.get("statut")
            statut_val = statut_raw.value if hasattr(statut_raw, "value") else str(statut_raw)
            statut_str = _STATUS_LABELS.get(statut_val, statut_val)

            titre_step = self._safe(f"  {step['id']}. {step['titre']}")
            org_step   = self._safe(step.get('organisme', '-'))
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*_DARK)
            pdf.cell(130, 7, titre_step)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 7, f"[{org_step}]",
                     new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*_LIGHT)
            delai_str = self._safe(step.get('delai', '-'))
            pdf.cell(0, 5,
                     f"     Statut : {statut_str}  |  "
                     f"Delai : {delai_str}  |  "
                     f"Frais : {step.get('frais', 0)} MAD",
                     new_x="LMARGIN", new_y="NEXT")
            docs = step.get("docs_requis", [])
            if docs:
                docs_str = self._safe(', '.join(docs))
                pdf.cell(0, 5, f"     Documents : {docs_str}",
                         new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*_DARK)
            pdf.ln(2)

    def _footer(self, pdf: FPDF):
        pdf.set_y(-18)
        pdf.set_draw_color(*_LIGHT)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*_LIGHT)
        pdf.cell(
            0, 5,
            "Genere par MAA - Morocco Administrative Agent  |  "
            "EMSI Casablanca 2026  |  Confidentiel",
            align="C",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section_title(self, pdf: FPDF, title: str):
        pdf.set_fill_color(*_GREY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_DARK)
        pdf.cell(0, 7, f"  {self._safe(title).upper()}", fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def _row(self, pdf: FPDF, label: str, value: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_DARK)
        pdf.cell(58, 6, f"  {self._safe(label)} :")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, self._safe(value), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*_DARK)

    @staticmethod
    def _safe(text: str) -> str:
        _MAP = {"\u2014": "-", "\u2013": "-", "\u2019": "'",
                "\u2018": "'", "\u201c": '"', "\u201d": '"'}
        for src, dst in _MAP.items():
            text = text.replace(src, dst)
        return text.encode("latin-1", errors="ignore").decode("latin-1")
