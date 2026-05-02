"""
resume_parser.py - PDF Text Extraction using pdfplumber
"""
import re
import pdfplumber

def extract_text_from_pdf(file_obj):
    """Extract and clean text from a PDF file object."""
    try:
        text_parts = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        raw = "\n".join(text_parts)
        return _clean(raw)
    except Exception as e:
        print(f"[resume_parser] Error: {e}")
        return ""

def _clean(text):
    if not text:
        return ""
    # Fix common ligatures
    replacements = {
        "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
        "\ufb04": "ffl", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove control characters except newlines and tabs
    text = re.sub(r'[^\x20-\x7E\n\t]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing whitespace from lines
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
