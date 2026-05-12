from datetime import datetime
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from services.i18n import PROCEDURE_TITLES_AR, STEP_STATUS_AR, t
from tools.doc_gen import PDFGenerator, _DARK, _GREEN, _GREY, _LIGHT

_ARIAL = Path("C:/Windows/Fonts/arial.ttf")
_ARABIC_FALLBACKS = [
    _ARIAL,
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/System/Library/Fonts/Arial.ttf"),
]


def _find_arabic_font() -> Path | None:
    for f in _ARABIC_FALLBACKS:
        if f.exists():
            return f
    return None


def _ar(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


class BilingualPDFGenerator(PDFGenerator):

    def generate_bilingual(
        self,
        procedure:      dict,
        collected_info: dict,
        plan:           list[dict],
        session_id:     str = "",
    ) -> bytes:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Page 1 : Français ──────────────────────────────────────────
        pdf.add_page()
        self._header(pdf, procedure, session_id)
        self._meta_section(pdf, procedure, plan)
        if collected_info:
            self._collected_section(pdf, collected_info)
        self._plan_section(pdf, plan)
        self._footer(pdf)

        # ── Page 2 : Arabe ─────────────────────────────────────────────
        font_path = _find_arabic_font()
        if font_path:
            pdf.add_font("Arabic", "", str(font_path))
            pdf.add_page()
            self._arabic_page(pdf, procedure, collected_info, plan, session_id)
            self._ar_footer(pdf)

        return bytes(pdf.output())

    # ------------------------------------------------------------------
    # Page arabe
    # ------------------------------------------------------------------

    def _arabic_page(
        self,
        pdf:            FPDF,
        procedure:      dict,
        collected_info: dict,
        plan:           list[dict],
        session_id:     str,
    ):
        # En-tête vert
        pdf.set_fill_color(*_GREEN)
        pdf.rect(0, 0, 210, 32, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arabic", "", 16)
        pdf.set_y(7)
        self._arc(pdf, 0, 10, _ar("وكيل إداري مغربي — MAA"), align="C")
        pdf.set_font("Arabic", "", 9)
        self._arc(pdf, 0, 5, _ar(t("pdf_header_sub", "ar")), align="C")
        pdf.set_text_color(*_DARK)
        pdf.set_y(38)

        # Titre procédure
        pid        = procedure.get("id", "")
        title_ar   = PROCEDURE_TITLES_AR.get(pid, self._safe(procedure.get("titre", "")))
        pdf.set_font("Arabic", "", 13)
        self._arc(pdf, 0, 9, _ar(title_ar))
        pdf.set_font("Arabic", "", 8)
        pdf.set_text_color(*_LIGHT)
        now_str = datetime.now().strftime("%d/%m/%Y")
        self._arc(pdf, 0, 5, _ar(f"{t('pdf_generated','ar')} {now_str}"))
        if session_id:
            self._arc(pdf, 0, 5, f"{session_id[:8]}...")
        pdf.set_text_color(*_DARK)
        pdf.ln(4)

        # Informations générales
        self._ar_section(pdf, t("pdf_section_meta", "ar"))
        orgs      = ", ".join(procedure.get("organisme", [])) or "-"
        frais_est = procedure.get("frais_est", {})
        total     = sum(s.get("frais", 0) for s in plan)
        self._arrow(pdf, t("pdf_orgs", "ar"),       self._safe(orgs))
        self._arrow(pdf, t("pdf_duration", "ar"),   self._safe(procedure.get("duree_est", "-")))
        self._arrow(pdf, t("pdf_fees_est", "ar"),
                    f"{frais_est.get('min', 0)} - {frais_est.get('max', 0)} MAD")
        self._arrow(pdf, t("pdf_fees_calc", "ar"),  f"{total} MAD")
        pdf.ln(4)

        # Informations collectées
        if collected_info:
            self._ar_section(pdf, t("pdf_section_info", "ar"))
            for key, val in collected_info.items():
                label = key.replace("_", " ").title()
                self._arrow(pdf, _ar(label), self._safe(str(val)))
            pdf.ln(4)

        # Plan des étapes
        self._ar_section(pdf, t("pdf_section_plan", "ar"))
        for step in plan:
            statut_raw = step.get("statut")
            statut_val = statut_raw.value if hasattr(statut_raw, "value") else str(statut_raw)
            statut_ar  = STEP_STATUS_AR.get(statut_val, statut_val)

            titre_ar = _ar(f"الخطوة {step['id']}: {self._safe(step['titre'])}")
            pdf.set_font("Arabic", "", 10)
            pdf.set_text_color(*_DARK)
            self._arc(pdf, 0, 7, titre_ar)

            pdf.set_font("Arabic", "", 8)
            pdf.set_text_color(*_LIGHT)
            info_line = _ar(f"{statut_ar} | {step.get('frais', 0)} MAD | {self._safe(step.get('delai', '-'))}")
            self._arc(pdf, 0, 5, info_line)
            docs = step.get("docs_requis", [])
            if docs:
                docs_str = _ar(self._safe(", ".join(docs)))
                self._arc(pdf, 0, 5, docs_str)
            pdf.set_text_color(*_DARK)
            pdf.ln(2)

    # ------------------------------------------------------------------
    # Helpers arabes
    # ------------------------------------------------------------------

    def _arc(self, pdf: FPDF, w: float, h: float, text: str, align: str = "R"):
        pdf.cell(w, h, text, align=align, new_x="LMARGIN", new_y="NEXT")

    def _ar_section(self, pdf: FPDF, title: str):
        pdf.set_fill_color(*_GREY)
        pdf.set_font("Arabic", "", 9)
        pdf.set_text_color(*_DARK)
        pdf.cell(0, 7, _ar(f"  {title}  "), fill=True, align="R",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def _arrow(self, pdf: FPDF, label: str, value: str):
        pdf.set_font("Arabic", "", 9)
        pdf.set_text_color(*_DARK)
        display = f"{value}  :  {_ar(label)}"
        pdf.cell(0, 6, display, align="R", new_x="LMARGIN", new_y="NEXT")

    def _ar_footer(self, pdf: FPDF):
        pdf.set_y(-18)
        pdf.set_draw_color(*_LIGHT)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Arabic", "", 7)
        pdf.set_text_color(*_LIGHT)
        pdf.cell(0, 5, _ar(t("pdf_footer", "ar")), align="C")
