"""utils.py - Shared utility functions"""

def safe_int(val, default=0):
    try:
        return int(val or default)
    except:
        return default

def safe_list(val):
    if isinstance(val, list):
        return val
    return []

def truncate(text, length=500):
    if not text:
        return ""
    return text[:length] + "..." if len(text) > length else text

def score_color(score):
    score = safe_int(score)
    if score >= 70: return "#10b981"
    if score >= 40: return "#f59e0b"
    return "#ef4444"

def score_label(score):
    score = safe_int(score)
    if score >= 80: return "Excellent"
    if score >= 65: return "Good"
    if score >= 50: return "Average"
    return "Needs Work"
