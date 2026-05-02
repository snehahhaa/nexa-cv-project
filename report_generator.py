"""
report_generator.py - NexaCV PDF Report Generator
"""
import io
from datetime import datetime
from reportlab.lib           import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles    import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units     import cm
from reportlab.platypus      import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums     import TA_CENTER, TA_LEFT

PURPLE = colors.HexColor("#6366f1")
GREEN  = colors.HexColor("#10b981")
RED    = colors.HexColor("#ef4444")
AMBER  = colors.HexColor("#f59e0b")
BLUE   = colors.HexColor("#0891b2")
DARK   = colors.HexColor("#0f172a")
SLATE  = colors.HexColor("#64748b")
LIGHT  = colors.HexColor("#f8fafc")
BORDER = colors.HexColor("#e2e8f0")
WHITE  = colors.white
PLUM   = colors.HexColor("#ede9fe")
GLIGHT = colors.HexColor("#d1fae5")
RLIGHT = colors.HexColor("#fee2e2")
ALIGHT = colors.HexColor("#fef3c7")
BLIGHT = colors.HexColor("#e0f2fe")
W = 17 * cm

def generate_pdf_report(username, resume_filename, ats_result, skills_data, ai_analysis) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm,
                            title="NexaCV Resume Analysis Report")
    story = _build(username, resume_filename, ats_result, skills_data, ai_analysis)
    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()

def _s(name, **kw):
    b = getSampleStyleSheet()
    return ParagraphStyle(name, parent=b["Normal"], **kw)

def _p(txt, style):
    return Paragraph(str(txt) if txt is not None else "", style)

def _ts(cmds):
    return TableStyle(cmds)

def _build(username, resume_filename, ats_result, skills_data, ai_analysis):
    now   = datetime.now().strftime("%B %d, %Y  %H:%M")
    score = int(ats_result.get("total_score") or 0)
    sub   = ats_result.get("sub_scores", {}) or {}
    grade = str(ats_result.get("grade") or "—")
    fb    = ((ats_result.get("feedback") or [""]))[0] or ""
    sc    = GREEN if score >= 70 else AMBER if score >= 40 else RED

    TITLE  = _s("TI", fontSize=22, textColor=DARK, fontName="Helvetica-Bold", spaceAfter=2)
    SUBT   = _s("SU", fontSize=10, textColor=SLATE, spaceAfter=10)
    H1     = _s("H1", fontSize=13, textColor=PURPLE, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    BODY   = _s("BD", fontSize=9, textColor=DARK, leading=14, spaceAfter=3)
    MUTED  = _s("MU", fontSize=9, textColor=SLATE, leading=14)
    BULLET = _s("BU", fontSize=9, textColor=DARK, leading=15, leftIndent=10, spaceAfter=3)
    DISC   = _s("DI", fontSize=7, textColor=SLATE, alignment=TA_CENTER)

    story = []

    story += [
        _p("NexaCV", TITLE),
        _p(f"Resume Analysis Report  •  {now}", SUBT),
        HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=10),
    ]

    info = Table([
        [_p("<b>Candidate</b>", MUTED), _p(username or "—", BODY)],
        [_p("<b>Resume</b>",    MUTED), _p(resume_filename or "—", BODY)],
        [_p("<b>Generated</b>", MUTED), _p(now, BODY)],
    ], colWidths=[3*cm, 14*cm])
    info.setStyle(_ts([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LIGHT,WHITE]),
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",    (0,0),(-1,-1), 0.25, BORDER),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [info, Spacer(1, 0.5*cm)]

    story.append(_p("ATS Compatibility Score", H1))
    banner = Table([[
        _p(str(score), ParagraphStyle("sc", parent=BODY, fontSize=44,
                                      textColor=sc, fontName="Helvetica-Bold",
                                      alignment=TA_CENTER)),
        _p(f"Grade\n{grade}", ParagraphStyle("gv", parent=BODY, fontSize=22,
                              textColor=PURPLE, fontName="Helvetica-Bold",
                              alignment=TA_CENTER)),
        _p(fb, ParagraphStyle("fb", parent=BODY, textColor=SLATE, leading=16)),
    ]], colWidths=[4*cm, 3*cm, 10*cm])
    banner.setStyle(_ts([
        ("BACKGROUND",    (0,0),(-1,-1), PLUM),
        ("BOX",           (0,0),(-1,-1), 1, PURPLE),
        ("LINEAFTER",     (0,0),(0,0),   0.5, PURPLE),
        ("LINEAFTER",     (1,0),(1,0),   0.5, PURPLE),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",         (0,0),(1,0),   "CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story += [banner, Spacer(1, 0.5*cm)]

    wmap = [
        ("skill_match","Skill Match","40%"),
        ("experience", "Experience","25%"),
        ("education",  "Education", "20%"),
        ("keyword",    "Keywords",  "15%"),
    ]
    WH = _s("WH", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_CENTER)
    rows = [[_p(h, WH) for h in ["Category","Score","Progress","Weight","Contribution"]]]
    for key, label, wt in wmap:
        v  = int(sub.get(key) or 0)
        wn = float(wt[:-1]) / 100
        bc = GREEN if v >= 70 else AMBER if v >= 40 else RED
        bar = "█" * int(v/10) + "░" * (10 - int(v/10))
        rows.append([
            _p(label, BODY),
            _p(str(v), ParagraphStyle("sv", parent=BODY, textColor=bc,
                                       fontName="Helvetica-Bold", alignment=TA_CENTER)),
            _p(bar, ParagraphStyle("br", parent=BODY, textColor=bc, fontName="Courier", fontSize=8)),
            _p(wt,  ParagraphStyle("wt", parent=BODY, textColor=SLATE, alignment=TA_CENTER)),
            _p(str(round(v*wn,1)), ParagraphStyle("ct", parent=BODY, alignment=TA_CENTER)),
        ])
    sub_tbl = Table(rows, colWidths=[4*cm, 1.5*cm, 7.5*cm, 2*cm, 2*cm])
    sub_tbl.setStyle(_ts([
        ("BACKGROUND",    (0,0),(-1,0),  DARK),
        ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT,WHITE]),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.25, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [sub_tbl, Spacer(1, 0.5*cm)]

    story.append(_p("Skills Analysis", H1))
    matched = skills_data.get("matched_skills") or []
    missing = skills_data.get("missing_skills") or []

    def skill_rows(items, accent, bg):
        rows = [[_p(f"• {s}", BULLET)] for s in (items or [])[:25]]
        if not rows:
            rows = [[_p("None detected.", MUTED)]]
        t = Table(rows, colWidths=[7.8*cm])
        t.setStyle(_ts([("BACKGROUND",(0,0),(-1,-1),bg),("BOX",(0,0),(-1,-1),0.5,accent),
                        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                        ("LEFTPADDING",(0,0),(-1,-1),8)]))
        return t

    sk = Table([
        [_p("<b>Matched Skills</b>", ParagraphStyle("mh",fontSize=9,textColor=GREEN,fontName="Helvetica-Bold")),
         _p(""),
         _p("<b>Missing Skills</b>", ParagraphStyle("rh",fontSize=9,textColor=RED,fontName="Helvetica-Bold"))],
        [skill_rows(matched,GREEN,GLIGHT), _p("",MUTED), skill_rows(missing,RED,RLIGHT)],
    ], colWidths=[8*cm,1*cm,8*cm])
    sk.setStyle(_ts([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),4)]))
    story += [sk, Spacer(1, 0.5*cm)]

    story.append(_p("AI-Generated Analysis", H1))
    story.append(_p("Analysis by Groq AI (LLaMA 3.3) based on your resume and job description.", MUTED))
    story.append(Spacer(1, 0.3*cm))

    for title, key, color, bg in [
        ("Strengths",              "strengths",      GREEN,  GLIGHT),
        ("Weaknesses",             "weaknesses",     AMBER,  ALIGHT),
        ("Missing Skills (AI)",    "missing_skills", RED,    RLIGHT),
        ("Recommended Keywords",   "keywords",       PURPLE, PLUM),
        ("Improvement Suggestions","suggestions",    BLUE,   BLIGHT),
    ]:
        items = ai_analysis.get(key) or []
        if not items:
            continue
        ts = _s(f"at_{key}", fontSize=11, textColor=color, fontName="Helvetica-Bold",
                spaceBefore=8, spaceAfter=5)
        story.append(_p(title, ts))
        t = Table([[_p(f"• {i}", BULLET)] for i in items], colWidths=[W])
        t.setStyle(_ts([("BACKGROUND",(0,0),(-1,-1),bg),("BOX",(0,0),(-1,-1),0.5,color),
                        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                        ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10)]))
        story.append(t)
        story.append(Spacer(1, 0.2*cm))

    story += [
        Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=0.5, color=BORDER),
        Spacer(1, 0.2*cm),
        _p("Generated by NexaCV — AI-powered resume analysis.", DISC),
    ]
    return story

def _hf(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(DARK)
    canvas.rect(0, h-1.2*cm, w, 1.2*cm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(WHITE)
    canvas.drawString(2*cm, h-0.78*cm, "NexaCV")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawRightString(w-2*cm, h-0.78*cm, "Resume Analysis Report")
    canvas.setStrokeColor(PURPLE)
    canvas.setLineWidth(2)
    canvas.line(0, h-1.2*cm, w, h-1.2*cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SLATE)
    canvas.drawCentredString(w/2, 0.6*cm, f"Page {doc.page}  |  Confidential")
    canvas.restoreState()
