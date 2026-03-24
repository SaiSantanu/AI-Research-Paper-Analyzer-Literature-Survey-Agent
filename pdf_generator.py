"""
pdf_generator.py - IEEE-style academic PDF generator.

Replaces the basic _generate_pdf() in bridge.py.
Import and call: generate_ieee_pdf(state, topic) -> bytes
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
    NextPageTemplate,
)
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Color palette (IEEE-inspired)
# ---------------------------------------------------------------------------
# Logo path - update this to wherever you save the logo
LOGO_PATH = "logo-1024x1024.png"   # place logo.png in same folder as bridge.py

C_BLACK      = colors.HexColor("#000000")
C_DARK       = colors.HexColor("#1a1a1a")
C_HEADING    = colors.HexColor("#003366")   # deep navy
C_ACCENT     = colors.HexColor("#004080")
C_RULE       = colors.HexColor("#003366")
C_LIGHT_GRAY = colors.HexColor("#f5f5f5")
C_MID_GRAY   = colors.HexColor("#cccccc")
C_TABLE_HEAD = colors.HexColor("#003366")
C_TABLE_ALT  = colors.HexColor("#eef2f7")
C_WHITE      = colors.white


# ---------------------------------------------------------------------------
# Page layout constants
# ---------------------------------------------------------------------------
PW, PH       = A4
MARGIN_OUT   = 2.0 * cm   # outer margin
MARGIN_IN    = 1.8 * cm   # inner margin (gutter)
MARGIN_TOP   = 2.5 * cm
MARGIN_BOT   = 2.5 * cm
COL_GAP      = 0.5 * cm

# Single-column width (cover + TOC + section titles)
SINGLE_W = PW - MARGIN_OUT - MARGIN_IN

# Two-column widths
TWO_COL_W = (SINGLE_W - COL_GAP) / 2


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def make_styles():
    s = {}

    # --- Body text (IEEE uses 9-10pt Times-Roman justified) ---
    s["body"] = ParagraphStyle(
        "body",
        fontName="Times-Roman", fontSize=9.5,
        leading=13, spaceAfter=4,
        alignment=TA_JUSTIFY,
        textColor=C_DARK,
    )
    s["body_sm"] = ParagraphStyle(
        "body_sm",
        parent=s["body"], fontSize=8.5, leading=11,
    )

    # --- Section heading (e.g. "I. INTRODUCTION") ---
    s["section"] = ParagraphStyle(
        "section",
        fontName="Times-Bold", fontSize=10,
        leading=14, spaceBefore=14, spaceAfter=4,
        alignment=TA_CENTER,
        textColor=C_HEADING,
        textTransform="uppercase",
    )

    # --- Sub-heading ---
    s["subsection"] = ParagraphStyle(
        "subsection",
        fontName="Times-Bold", fontSize=9.5,
        leading=13, spaceBefore=8, spaceAfter=3,
        alignment=TA_LEFT,
        textColor=C_DARK,
    )

    # --- Paper title on cover ---
    s["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Times-Bold", fontSize=22,
        leading=28, spaceAfter=8,
        alignment=TA_CENTER,
        textColor=C_HEADING,
    )
    s["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle",
        fontName="Times-Roman", fontSize=12,
        leading=16, spaceAfter=6,
        alignment=TA_CENTER,
        textColor=C_DARK,
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta",
        fontName="Times-Roman", fontSize=10,
        leading=14, spaceAfter=4,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
    )

    # --- Abstract box ---
    s["abstract_title"] = ParagraphStyle(
        "abstract_title",
        fontName="Times-Bold", fontSize=9,
        leading=12, spaceAfter=4,
        alignment=TA_CENTER,
        textColor=C_DARK,
        textTransform="uppercase",
    )
    s["abstract_body"] = ParagraphStyle(
        "abstract_body",
        fontName="Times-Italic", fontSize=9,
        leading=12, spaceAfter=0,
        alignment=TA_JUSTIFY,
        textColor=C_DARK,
        leftIndent=6, rightIndent=6,
    )

    # --- TOC ---
    s["toc_title"] = ParagraphStyle(
        "toc_title",
        fontName="Times-Bold", fontSize=13,
        leading=18, spaceAfter=10,
        alignment=TA_CENTER,
        textColor=C_HEADING,
    )
    s["toc_entry"] = ParagraphStyle(
        "toc_entry",
        fontName="Times-Roman", fontSize=10,
        leading=16, spaceAfter=0,
        textColor=C_DARK,
    )
    s["toc_entry_bold"] = ParagraphStyle(
        "toc_entry_bold",
        fontName="Times-Bold", fontSize=10,
        leading=16, spaceAfter=0,
        textColor=C_DARK,
    )

    # --- Caption ---
    s["caption"] = ParagraphStyle(
        "caption",
        fontName="Times-Italic", fontSize=8.5,
        leading=11, spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444"),
    )

    # --- Table cell ---
    s["cell"] = ParagraphStyle(
        "cell",
        fontName="Times-Roman", fontSize=8,
        leading=10, spaceAfter=0,
        alignment=TA_LEFT,
        textColor=C_DARK,
    )
    s["cell_hdr"] = ParagraphStyle(
        "cell_hdr",
        fontName="Times-Bold", fontSize=8,
        leading=10, spaceAfter=0,
        alignment=TA_CENTER,
        textColor=C_WHITE,
    )

    return s


# ---------------------------------------------------------------------------
# Page number canvas
# ---------------------------------------------------------------------------
class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        rl_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page_num = self._pageNumber
        # Skip cover page (page 1)
        if page_num <= 1:
            return
        self.saveState()
        # Footer line
        self.setStrokeColor(C_RULE)
        self.setLineWidth(0.5)
        self.line(MARGIN_OUT, MARGIN_BOT - 4*mm,
                  PW - MARGIN_OUT, MARGIN_BOT - 4*mm)
        # Page number center
        self.setFont("Times-Roman", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawCentredString(PW / 2, MARGIN_BOT - 9*mm,
                               str(page_num) + " of " + str(page_count))
        self.restoreState()


# ---------------------------------------------------------------------------
# Header callback (runs on every page except cover)
# ---------------------------------------------------------------------------
def make_header_footer(topic, doc_title="Literature Review"):
    def on_page(canv, doc):
        if doc.page <= 1:
            return
        canv.saveState()

        LOGO_H = 18   # logo height in points in header
        LOGO_W = 18

        # Draw logo in header left if file exists
        import os
        if os.path.exists(LOGO_PATH):
            try:
                canv.drawImage(
                    LOGO_PATH,
                    MARGIN_OUT,
                    PH - MARGIN_TOP + 2*mm,
                    width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True,
                    mask="auto"
                )
                title_x = MARGIN_OUT + LOGO_W + 4
            except Exception:
                title_x = MARGIN_OUT
        else:
            title_x = MARGIN_OUT

        # Top rule
        canv.setStrokeColor(C_RULE)
        canv.setLineWidth(1)
        canv.line(MARGIN_OUT, PH - MARGIN_TOP + 4*mm,
                  PW - MARGIN_OUT, PH - MARGIN_TOP + 4*mm)

        # Left: document title (after logo)
        canv.setFont("Times-Italic", 8)
        canv.setFillColor(colors.HexColor("#555555"))
        canv.drawString(title_x, PH - MARGIN_TOP + 6*mm, doc_title)

        # Right: topic
        canv.drawRightString(PW - MARGIN_OUT, PH - MARGIN_TOP + 6*mm,
                             topic[:55])
        canv.restoreState()
    return on_page


# ---------------------------------------------------------------------------
# Helper: clean text for ReportLab XML
# ---------------------------------------------------------------------------
def rl_safe(text):
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def clean_extraction(text, max_chars=600):
    """
    Smart cleaner for RAG-extracted text.
    Splits on [...] chunk separators, scores each chunk,
    removes boilerplate, fixes mid-sentence starts.
    """
    import re

    if not text:
        return "Not available."

    # Split on RAG chunk separators [...] or [...]
    chunks = re.split(r"\s*\[\.{2,3}\]\s*", text)

    BAD = [
        "@", "University", "Institute", "College", "Laboratory",
        "Department", "School of", "Universidade", "UTFPR", "UEL",
        "A R T I C L E", "A B S T R A C T", "Index Terms",
        "Av.", "Rodovia", "Km ",
    ]
    GOOD = [
        "method", "approach", "result", "achiev", "accurac",
        "propos", "dataset", "model", "train", "evaluat",
        "perform", "experiment", "limit", "future", "find",
        "show", "demonstrat", "analys", "detect", "predict",
        "paper", "study", "work", "present", "measur",
    ]

    def score_chunk(chunk):
        s = 0
        c_low = chunk.lower()
        for p in BAD:
            if p.lower() in c_low:
                s -= 2
        for p in GOOD:
            if p in c_low:
                s += 1
        stripped = chunk.strip()
        if stripped and stripped[0].isupper():
            s += 2
        if len(stripped) < 40:
            s -= 3
        return s

    scored = sorted(
        [(score_chunk(c), c.strip()) for c in chunks if len(c.strip()) > 20],
        reverse=True
    )

    selected = []
    total = 0
    for _, chunk in scored:
        if total >= max_chars:
            break
        # Strip inline boilerplate
        chunk = re.sub(r"Index Terms[^.]*\.", "", chunk, flags=re.IGNORECASE)
        chunk = re.sub(r"A R T I C L E I N F[^\n]*", "", chunk)
        chunk = re.sub(r"Keywords?:[^\n]*", "", chunk, flags=re.IGNORECASE)
        chunk = re.sub(r"Abstract[-:]?\s*", "", chunk, flags=re.IGNORECASE)
        chunk = re.sub(r"\s+", " ", chunk).strip()
        # Fix mid-sentence chunk starts
        if chunk and chunk[0].islower():
            match = re.search(r"(?<=[.!?] )[A-Z]", chunk)
            if match:
                chunk = chunk[match.start() - 1:]
            else:
                chunk = chunk[0].upper() + chunk[1:]
        if len(chunk) > 30:
            selected.append(chunk)
            total += len(chunk)

    result = " ".join(selected).strip()
    result = re.sub(r"\s+", " ", result)

    if not result or len(result) < 20:
        return "Content extraction incomplete for this paper."
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(" ", 1)[0] + "..."
    return result


def build_cover(story, styles, topic, paper_count, date_str):
    import os

    # Top spacer
    story.append(Spacer(1, 2.0 * cm))

    # Logo centered on cover
    if os.path.exists(LOGO_PATH):
        try:
            logo = RLImage(LOGO_PATH, width=2.2*cm, height=2.2*cm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 0.4 * cm))
        except Exception:
            pass

    # App name below logo
    story.append(Paragraph("ScholarAI", styles["cover_meta"]))
    story.append(Spacer(1, 0.6 * cm))

    # IEEE-style top rule
    story.append(HRFlowable(width="100%", thickness=2,
                             color=C_HEADING, spaceAfter=16))

    # Main title
    story.append(Paragraph(
        "Literature Review:<br/>" + rl_safe(topic),
        styles["cover_title"]
    ))

    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_MID_GRAY, spaceBefore=8, spaceAfter=20))

    # Meta block
    story.append(Paragraph("Generated by ScholarAI", styles["cover_subtitle"]))
    story.append(Spacer(1, 0.3 * cm))

    meta_data = [
        ["Date", date_str],
        ["Papers Analysed", str(paper_count)],
        ["Source", "arXiv.org"],
        ["Pipeline", "LangGraph + RAG + ChromaDB"],
    ]
    meta_table = Table(
        [[Paragraph("<b>" + k + "</b>", styles["body"]),
          Paragraph(v, styles["body"])]
         for k, v in meta_data],
        colWidths=[4 * cm, 8 * cm],
        hAlign="CENTER",
    )
    meta_table.setStyle(TableStyle([
        ("GRID",        (0, 0), (-1, -1), 0.4, C_MID_GRAY),
        ("BACKGROUND",  (0, 0), (0, -1), C_LIGHT_GRAY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)

    # Abstract / description box
    story.append(Spacer(1, 1.2 * cm))
    abstract_text = (
        "This document presents an automated literature review compiled by ScholarAI, "
        "a multi-agent AI system. The pipeline autonomously searches arXiv, downloads "
        "and parses research papers, extracts methodology, results and limitations using "
        "Retrieval-Augmented Generation (RAG), and synthesizes findings into a structured "
        "academic survey. The review employs a LangGraph-based orchestration with an "
        "iterative Reviewer/Reviser quality control loop."
    )
    abstract_box = Table(
        [[Paragraph("Abstract", styles["abstract_title"])],
         [Paragraph(abstract_text, styles["abstract_body"])]],
        colWidths=[SINGLE_W - 2 * cm],
        hAlign="CENTER",
    )
    abstract_box.setStyle(TableStyle([
        ("BOX",         (0, 0), (-1, -1), 0.8, C_HEADING),
        ("BACKGROUND",  (0, 0), (-1, -1), C_LIGHT_GRAY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LINEBELOW",    (0, 0), (-1, 0),  0.5, C_MID_GRAY),
    ]))
    story.append(abstract_box)

    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=C_HEADING, spaceAfter=0))
    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Table of Contents
# ---------------------------------------------------------------------------
def build_toc(story, styles, extractions):
    story.append(Paragraph("Table of Contents", styles["toc_title"]))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=C_HEADING, spaceAfter=12))

    sections = [
        ("I.",   "Introduction",           "3"),
        ("II.",  "Methodology Overview",   "3"),
    ]
    for i, ext in enumerate(extractions, 1):
        roman = ["III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][min(i-1, 7)]
        sections.append((roman + ".", ext["title"][:60] + ("..." if len(ext["title"]) > 60 else ""), "-"))

    sections.append(("",  "Comparison Table", "-"))
    sections.append(("",  "Conclusion",        "-"))

    toc_rows = []
    for num, title, page in sections:
        is_bold = num != ""
        style   = styles["toc_entry_bold"] if is_bold else styles["toc_entry"]
        indent  = 0 if is_bold else 16
        toc_rows.append(Table(
            [[Paragraph(num, style),
              Paragraph(title, ParagraphStyle("te", parent=style, leftIndent=indent)),
              Paragraph(page,  style)]],
            colWidths=[1.2*cm, SINGLE_W - 2.4*cm, 1.2*cm],
        ))
        toc_rows[-1].setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.3, C_MID_GRAY),
        ]))

    for row in toc_rows:
        story.append(row)

    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Introduction section
# ---------------------------------------------------------------------------
def build_introduction(story, styles, topic, extractions):
    story.append(Paragraph("I. Introduction", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_RULE, spaceAfter=8))

    intro = (
        "This literature review presents a systematic survey of recent research on <i>"
        + rl_safe(topic) +
        "</i>. The survey was generated automatically by the ScholarAI pipeline, which "
        "searches arXiv, extracts structured information from each paper using "
        "Retrieval-Augmented Generation (RAG), and synthesizes findings into a coherent review. "
        "A total of " + str(len(extractions)) + " papers were identified and analysed. "
        "For each paper, the methodology, key results, and limitations are extracted and "
        "presented. A comparative summary table is provided at the end of this document."
    )
    story.append(Paragraph(intro, styles["body"]))
    story.append(Spacer(1, 0.3 * cm))


# ---------------------------------------------------------------------------
# Per-paper sections
# ---------------------------------------------------------------------------
def build_paper_section(story, styles, ext, index):
    roman_map = {1:"III", 2:"IV", 3:"V", 4:"VI", 5:"VII", 6:"VIII", 7:"IX", 8:"X"}
    roman = roman_map.get(index, str(index + 2))

    title_short = ext["title"] if len(ext["title"]) <= 80 else ext["title"][:77] + "..."

    block = []

    # Section header
    block.append(Paragraph(
        roman + ". " + rl_safe(title_short),
        styles["section"]
    ))
    block.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_RULE, spaceAfter=8))

    # Sub-sections
    for field, label in [
        ("methodology", "A. Methodology"),
        ("results",     "B. Key Results"),
        ("limitations", "C. Limitations and Future Work"),
    ]:
        raw = ext.get(field, "")
        text = clean_extraction(raw, max_chars=700)
        block.append(Paragraph(label, styles["subsection"]))
        block.append(Paragraph(rl_safe(text), styles["body"]))
        block.append(Spacer(1, 0.15 * cm))

    story.append(KeepTogether(block[:4]))   # keep heading + methodology together
    for item in block[4:]:
        story.append(item)
    story.append(Spacer(1, 0.4 * cm))


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------
def build_comparison_table(story, styles, extractions):
    story.append(PageBreak())
    story.append(Paragraph("Comparison Table", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_RULE, spaceAfter=10))
    story.append(Paragraph(
        "Table I summarizes the methodology, key results, and limitations "
        "of all papers analysed in this review.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Header row
    hdr = [
        Paragraph("Paper", styles["cell_hdr"]),
        Paragraph("Methodology", styles["cell_hdr"]),
        Paragraph("Key Results", styles["cell_hdr"]),
        Paragraph("Limitations", styles["cell_hdr"]),
    ]

    col_w = [
        SINGLE_W * 0.22,
        SINGLE_W * 0.28,
        SINGLE_W * 0.26,
        SINGLE_W * 0.24,
    ]

    data = [hdr]
    for i, ext in enumerate(extractions):
        short_title = ext["title"][:55] + "..." if len(ext["title"]) > 55 else ext["title"]
        row = [
            Paragraph("<b>" + rl_safe(short_title) + "</b>", styles["cell"]),
            Paragraph(rl_safe(clean_extraction(ext.get("methodology", ""), 200)), styles["cell"]),
            Paragraph(rl_safe(clean_extraction(ext.get("results",     ""), 200)), styles["cell"]),
            Paragraph(rl_safe(clean_extraction(ext.get("limitations", ""), 150)), styles["cell"]),
        ]
        data.append(row)

    table = Table(data, colWidths=col_w, repeatRows=1)
    row_bg = []
    for i in range(1, len(data)):
        bg = C_TABLE_ALT if i % 2 == 0 else C_WHITE
        row_bg.append(("BACKGROUND", (0, i), (-1, i), bg))

    table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0),  C_TABLE_HEAD),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  C_WHITE),
        # Grid
        ("GRID",         (0, 0), (-1, -1), 0.4, C_MID_GRAY),
        ("LINEBELOW",    (0, 0), (-1, 0),  1.2, C_HEADING),
        # Padding
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ] + row_bg))

    story.append(table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("TABLE I: Comparison of analysed papers.", styles["caption"]))


# ---------------------------------------------------------------------------
# Conclusion
# ---------------------------------------------------------------------------
def build_conclusion(story, styles, topic, extractions):
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Conclusion", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_RULE, spaceAfter=8))

    titles = ", ".join("<i>" + rl_safe(e["title"][:40]) + "...</i>"
                       for e in extractions)
    conclusion = (
        "This survey reviewed " + str(len(extractions)) + " papers on <i>" +
        rl_safe(topic) + "</i>, including " + titles + ". "
        "The reviewed works collectively advance the state of the art through "
        "diverse methodological approaches and experimental evaluations. "
        "Key themes include novel architectural designs, improved training strategies, "
        "and application-specific adaptations. "
        "Future research directions identified across papers include scalability to "
        "larger datasets, reduction of computational overhead, and generalization "
        "to unseen domains. This review was generated automatically by ScholarAI "
        "and is intended as a starting point for deeper manual investigation."
    )
    story.append(Paragraph(conclusion, styles["body"]))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_ieee_pdf(state: dict, topic: str) -> bytes:
    """
    Generate an IEEE-style academic PDF from pipeline state.
    Returns PDF as bytes.
    """
    extractions = state.get("extractions", [])
    paper_count = len(state.get("papers", extractions))
    date_str    = datetime.now().strftime("%B %d, %Y")

    # If no extractions, fall back to report text parsing
    if not extractions and state.get("final_report"):
        return _fallback_pdf(state["final_report"], topic)

    buf    = BytesIO()
    styles = make_styles()

    # -- Document with single-column full-width frame ----------------------
    single_frame = Frame(
        MARGIN_OUT, MARGIN_BOT,
        SINGLE_W, PH - MARGIN_TOP - MARGIN_BOT,
        id="single",
    )

    on_page = make_header_footer(topic)

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN_OUT,
        rightMargin=MARGIN_IN,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOT,
        title="Literature Review: " + topic,
        author="ScholarAI",
        subject=topic,
    )

    cover_template = PageTemplate(
        id="cover",
        frames=[single_frame],
        onPage=lambda c, d: None,   # no header on cover
    )
    body_template = PageTemplate(
        id="body",
        frames=[single_frame],
        onPage=on_page,
    )
    doc.addPageTemplates([cover_template, body_template])

    # -- Build story -------------------------------------------------------
    story = []

    # Cover
    story.append(NextPageTemplate("body"))
    build_cover(story, styles, topic, paper_count, date_str)

    # TOC
    build_toc(story, styles, extractions)

    # Introduction + Methodology overview
    build_introduction(story, styles, topic, extractions)

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("II. Methodology Overview", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_RULE, spaceAfter=8))
    overview = (
        "The papers reviewed in this survey employ a variety of methodological approaches. "
        "Each paper is analysed in detail in the sections that follow. "
        "For a side-by-side comparison of all papers, refer to the Comparison Table "
        "at the end of this document."
    )
    story.append(Paragraph(overview, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # Per-paper sections
    for i, ext in enumerate(extractions, 1):
        build_paper_section(story, styles, ext, i)

    # Comparison table
    build_comparison_table(story, styles, extractions)

    # Conclusion
    build_conclusion(story, styles, topic, extractions)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fallback (when extractions not available, just format the report text)
# ---------------------------------------------------------------------------
def _fallback_pdf(report: str, topic: str) -> bytes:
    from reportlab.platypus import SimpleDocTemplate
    buf    = BytesIO()
    styles = make_styles()
    doc    = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=MARGIN_OUT, rightMargin=MARGIN_IN,
                                topMargin=MARGIN_TOP,  bottomMargin=MARGIN_BOT)
    story = [
        Paragraph("Literature Review: " + rl_safe(topic), styles["cover_title"]),
        Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=1, color=C_RULE, spaceAfter=12),
    ]
    for line in report.split("\n"):
        s = line.strip()
        if not s:
            story.append(Spacer(1, 4))
        elif s.startswith("## "):
            story.append(Paragraph(rl_safe(s[3:]), styles["section"]))
        elif s.startswith("# "):
            story.append(Paragraph(rl_safe(s[2:]), styles["section"]))
        elif s.startswith("**") and s.endswith("**"):
            story.append(Paragraph(rl_safe(s.replace("**","")), styles["subsection"]))
        else:
            story.append(Paragraph(rl_safe(s), styles["body"]))
    doc.build(story)
    return buf.getvalue()