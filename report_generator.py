"""
report_generator.py - NexaCV PDF Report Generator
Original working alignment + NexaCV branding.
"""

import io
from datetime import datetime
from typing import Dict, List

from reportlab.lib          import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles   import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units    import cm
from reportlab.platypus     import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums    import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colour palette ────────────────────────────────────────────────────────────
PURPLE       = colors.HexColor("#6366f1")
PURPLE_LIGHT = colors.HexColor("#ede9fe")
GREEN        = colors.HexColor("#22c55e")
GREEN_LIGHT  = colors.HexColor("#dcfce7")
RED          = colors.HexColor("#ef4444")
RED_LIGHT    = colors.HexColor("#fee2e2")
YELLOW       = colors.HexColor("#f59e0b")
YELLOW_LIGHT = colors.HexColor("#fffbeb")
BLUE         = colors.HexColor("#0891b2")
BLUE_LIGHT   = colors.HexColor("#e0f2fe")
DARK         = colors.HexColor("#0f172a")
SLATE        = colors.HexColor("#64748b")
LIGHT_BG     = colors.HexColor("#f8fafc")
WHITE        = colors.white


def generate_pdf_report(
    username:        str,
    resume_filename: str,
    ats_result:      Dict,
    skills_data:     Dict,
    ai_analysis:     Dict,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="NexaCV Resume Analysis Report",
        author="NexaCV",
    )
    styles = _build_styles()
    story  = _build_story(styles, username, resume_filename, ats_result, skills_data, ai_analysis)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


# ── Style definitions ─────────────────────────────────────────────────────────
def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title":       ParagraphStyle("title",       parent=base["Title"],
                                      fontSize=22, textColor=DARK,
                                      spaceAfter=4, fontName="Helvetica-Bold"),
        "subtitle":    ParagraphStyle("subtitle",    parent=base["Normal"],
                                      fontSize=10, textColor=SLATE,
                                      spaceAfter=12),
        "h1":          ParagraphStyle("h1",          parent=base["Heading1"],
                                      fontSize=14, textColor=PURPLE,
                                      fontName="Helvetica-Bold",
                                      spaceBefore=14, spaceAfter=6,
                                      borderPad=4),
        "h2":          ParagraphStyle("h2",          parent=base["Heading2"],
                                      fontSize=11, textColor=DARK,
                                      fontName="Helvetica-Bold",
                                      spaceBefore=8, spaceAfter=4),
        "body":        ParagraphStyle("body",        parent=base["Normal"],
                                      fontSize=9,  textColor=DARK,
                                      leading=14,  spaceAfter=3),
        "bullet":      ParagraphStyle("bullet",      parent=base["Normal"],
                                      fontSize=9,  textColor=DARK,
                                      leading=14,  leftIndent=12,
                                      bulletIndent=2, spaceAfter=2),
        "score_large": ParagraphStyle("score_large", parent=base["Normal"],
                                      fontSize=42, textColor=PURPLE,
                                      fontName="Helvetica-Bold",
                                      alignment=TA_CENTER),
        "caption":     ParagraphStyle("caption",     parent=base["Normal"],
                                      fontSize=8,  textColor=SLATE,
                                      alignment=TA_CENTER),
    }


# ── Story builder ─────────────────────────────────────────────────────────────
def _build_story(styles, username, resume_filename, ats_result, skills_data, ai_analysis):
    story = []
    now   = datetime.now().strftime("%B %d, %Y  %H:%M")
    score = int(ats_result.get("total_score") or 0)
    sub   = ats_result.get("sub_scores",  {}) or {}
    grade = str(ats_result.get("grade",   "—") or "—")
    fb    = ((ats_result.get("feedback") or [""]))[0] or ""

    score_colour = GREEN if score >= 70 else YELLOW if score >= 40 else RED

    # ── Cover header ──────────────────────────────────────────────────────────
    story += [
        Paragraph("NexaCV", styles["title"]),
        Paragraph(f"Resume Analysis Report  •  Generated {now}", styles["subtitle"]),
        HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=8),
    ]

    # ── Metadata table ────────────────────────────────────────────────────────
    meta = [
        ["Candidate",   username or "—"],
        ["Resume file", resume_filename or "—"],
        ["Generated",   now],
    ]
    meta_tbl = Table(meta, colWidths=[4*cm, 12*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0),(-1,-1), 9),
        ("TEXTCOLOR", (0,0),(0,-1),  SLATE),
        ("TEXTCOLOR", (1,0),(1,-1),  DARK),
        ("FONTNAME",  (0,0),(0,-1),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [LIGHT_BG, WHITE]),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 4),
        ("TOPPADDING",     (0,0),(-1,-1), 4),
        ("LEFTPADDING",    (0,0),(-1,-1), 6),
    ]))
    story += [meta_tbl, Spacer(1, 0.5*cm)]

    # ── ATS Score section ─────────────────────────────────────────────────────
    story.append(Paragraph("ATS Compatibility Score", styles["h1"]))

    score_data = [[
        Paragraph(f"{score}", ParagraphStyle("sc", parent=styles["score_large"],
                                             textColor=score_colour)),
        Paragraph(f"Grade\n{grade}", ParagraphStyle("gv", fontSize=22,
                  textColor=PURPLE, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(fb or "", styles["body"]),
    ]]
    score_tbl = Table(score_data, colWidths=[4*cm, 4*cm, 8*cm])
    score_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",         (0,0),(1,0),   "CENTER"),
        ("BACKGROUND",    (0,0),(-1,-1), PURPLE_LIGHT),
        ("BOX",           (0,0),(-1,-1), 0.5, PURPLE),
        ("LINEAFTER",     (0,0),(0,0),   0.5, PURPLE),
        ("LINEAFTER",     (1,0),(1,0),   0.5, PURPLE),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story += [score_tbl, Spacer(1, 0.4*cm)]

    # ── Sub-scores table ──────────────────────────────────────────────────────
    sub_headers = [
        Paragraph("<b>Category</b>",      styles["body"]),
        Paragraph("<b>Score (/100)</b>",  styles["body"]),
        Paragraph("<b>Weight</b>",        styles["body"]),
        Paragraph("<b>Contribution</b>",  styles["body"]),
    ]
    sub_rows = [sub_headers]
    weights_map = {"skill_match": "40%", "experience": "25%", "education": "20%", "keyword": "15%"}
    labels_map  = {"skill_match": "Skill Match", "experience": "Experience",
                   "education": "Education", "keyword": "Keyword Optimisation"}
    for key in ["skill_match", "experience", "education", "keyword"]:
        val = int(sub.get(key) or 0)
        bar = "█" * int(val / 10) + "░" * (10 - int(val / 10))
        sub_rows.append([
            Paragraph(labels_map[key], styles["body"]),
            Paragraph(f"{val}  {bar}", ParagraphStyle("bar", fontSize=8,
                      textColor=GREEN if val>=70 else YELLOW if val>=40 else RED,
                      fontName="Courier")),
            Paragraph(weights_map[key], styles["body"]),
            Paragraph(f"{round(val * float(weights_map[key][:-1]) / 100, 1)}", styles["body"]),
        ])

    sub_tbl = Table(sub_rows, colWidths=[5*cm, 6*cm, 3*cm, 3*cm])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  DARK),
        ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT_BG, WHITE]),
        ("GRID",          (0,0),(-1,-1), 0.25, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]))
    story += [sub_tbl, Spacer(1, 0.5*cm)]

    # ── Skills section ────────────────────────────────────────────────────────
    story.append(Paragraph("Skills Analysis", styles["h1"]))

    matched = skills_data.get("matched_skills") or []
    missing = skills_data.get("missing_skills") or []

    skills_layout = [[
        _skills_block("Matched Skills", matched, GREEN,  GREEN_LIGHT,  styles),
        _skills_block("Missing Skills", missing, RED,    RED_LIGHT,    styles),
    ]]
    skills_tbl = Table(skills_layout, colWidths=[8*cm, 8*cm])
    skills_tbl.setStyle(TableStyle([("VALIGN", (0,0),(-1,-1), "TOP"),
                                    ("LEFTPADDING",  (0,0),(-1,-1), 0),
                                    ("RIGHTPADDING", (0,0),(-1,-1), 0),]))
    story += [skills_tbl, Spacer(1, 0.5*cm)]

    # ── AI Analysis sections ──────────────────────────────────────────────────
    story.append(Paragraph("AI-Generated Analysis", styles["h1"]))
    story.append(Paragraph(
        "The following analysis was generated by Groq AI (LLaMA 3.3) based on your resume and job description.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.3*cm))

    ai_sections = [
        ("Strengths",               "strengths",      GREEN,  GREEN_LIGHT),
        ("Weaknesses",              "weaknesses",     YELLOW, YELLOW_LIGHT),
        ("Missing Skills (AI view)","missing_skills", RED,    RED_LIGHT),
        ("Recommended Keywords",    "keywords",       PURPLE, PURPLE_LIGHT),
        ("Improvement Suggestions", "suggestions",    BLUE,   BLUE_LIGHT),
    ]
    for title, key, accent, bg in ai_sections:
        items = ai_analysis.get(key) or []
        if not items:
            continue
        story.append(KeepTogether(_ai_section_block(title, items, accent, bg, styles)))

    # ── Footer note ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=1, color=SLATE),
        Spacer(1, 0.2*cm),
        Paragraph(
            "This report was generated by NexaCV. "
            "Results are indicative and should be used as one input in your job search.",
            ParagraphStyle("disclaimer", fontSize=7, textColor=SLATE, alignment=TA_CENTER),
        ),
    ]

    return story


# ── Block helpers ─────────────────────────────────────────────────────────────
def _skills_block(title, skills, accent, bg, styles):
    rows = [[Paragraph(f"<b>{title}</b>",
                        ParagraphStyle("sh", fontSize=9, textColor=accent,
                                       fontName="Helvetica-Bold"))]]
    if skills:
        for s in (skills or [])[:20]:
            rows.append([Paragraph(f"• {s}", styles["bullet"])])
    else:
        rows.append([Paragraph("None detected.", styles["body"])])

    t = Table(rows, colWidths=[7.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("BOX",           (0,0),(-1,-1), 0.5, accent),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]))
    return t


def _ai_section_block(title, items, accent, bg, styles):
    block = [
        Paragraph(title, ParagraphStyle("at", fontSize=11, textColor=accent,
                                        fontName="Helvetica-Bold",
                                        spaceBefore=8, spaceAfter=4)),
    ]
    for item in (items or []):
        block.append(Paragraph(f"• {item}", styles["bullet"]))
    block.append(Spacer(1, 0.2*cm))
    return block


# ── Page decorators ───────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(DARK)
    canvas.rect(0, h - 1.2*cm, w, 1.2*cm, fill=1, stroke=0)

    # NexaCV branding
    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(WHITE)
    canvas.drawString(2*cm, h - 0.78*cm, "NexaCV")

    # Purple dot accent
    canvas.setFillColor(PURPLE)
    canvas.circle(2*cm + 50, h - 0.78*cm + 3, 3, fill=1, stroke=0)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawRightString(w - 2*cm, h - 0.78*cm, "Resume Analysis Report")

    # Purple accent line
    canvas.setStrokeColor(PURPLE)
    canvas.setLineWidth(2)
    canvas.line(0, h - 1.2*cm, w, h - 1.2*cm)

    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SLATE)
    canvas.drawCentredString(w / 2, 0.7*cm, f"Page {doc.page}")
    canvas.restoreState()
