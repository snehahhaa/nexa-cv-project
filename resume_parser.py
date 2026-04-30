"""
resume_parser.py - PDF Resume Text Extraction
Uses pdfplumber to extract clean text from uploaded PDF resumes.
"""

import pdfplumber
import re
import io
from typing import Optional


# ── Public API ────────────────────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> Optional[str]:
    """
    Extract all text from a PDF file uploaded via Streamlit.

    Parameters
    ----------
    uploaded_file : UploadedFile
        A Streamlit UploadedFile object (BytesIO-compatible).

    Returns
    -------
    str or None
        Cleaned plain text, or None if extraction failed.
    """
    try:
        # Read bytes from Streamlit's UploadedFile
        pdf_bytes = uploaded_file.read()
        text_parts = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        if not text_parts:
            return None

        raw_text = "\n".join(text_parts)
        return _clean_text(raw_text)

    except Exception as exc:
        print(f"[resume_parser] PDF extraction error: {exc}")
        return None


# ── Text cleaning ─────────────────────────────────────────────────────────────
def _clean_text(text: str) -> str:
    """
    Normalise whitespace and remove noise characters from extracted PDF text.
    """
    # Replace common ligatures / unicode issues
    replacements = {
        "\ufb01": "fi", "\ufb02": "fl",
        "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2022": "•",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # Collapse multiple blank lines → single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalise spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()


# ── Section detection (optional helper used by ats_score) ────────────────────
SECTION_HEADERS = {
    "experience":  r"(work\s+experience|professional\s+experience|employment\s+history|experience)",
    "education":   r"(education|academic\s+background|qualifications)",
    "skills":      r"(skills|technical\s+skills|core\s+competencies|expertise)",
    "projects":    r"(projects|personal\s+projects|side\s+projects)",
    "summary":     r"(summary|objective|profile|about\s+me)",
    "certifications": r"(certifications|certificates|licenses)",
}


def detect_sections(text: str) -> dict:
    """
    Heuristically split resume text into named sections.

    Returns a dict mapping section name → text content.
    """
    sections: dict = {}
    lines = text.splitlines()
    current_section = "header"
    buffer: list = []

    for line in lines:
        line_lower = line.lower().strip()
        matched_section = None
        for section, pattern in SECTION_HEADERS.items():
            if re.fullmatch(pattern, line_lower):
                matched_section = section
                break

        if matched_section:
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = matched_section
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def extract_contact_info(text: str) -> dict:
    """
    Extract basic contact information from resume text.
    Returns a dict with email, phone, linkedin keys (or None).
    """
    email_pattern   = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    phone_pattern   = r"(\+?\d[\d\s\-().]{7,}\d)"
    linkedin_pattern = r"linkedin\.com/in/[\w\-]+"

    email   = re.search(email_pattern,   text)
    phone   = re.search(phone_pattern,   text)
    linkedin = re.search(linkedin_pattern, text, re.IGNORECASE)

    return {
        "email":    email.group()   if email    else None,
        "phone":    phone.group()   if phone    else None,
        "linkedin": linkedin.group() if linkedin else None,
    }
