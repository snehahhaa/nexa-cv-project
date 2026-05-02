"""
ats_score.py - ATS Compatibility Score Calculator
Weighted 4-dimension scoring algorithm
"""
import re

WEIGHTS = {"skill_match": 0.40, "experience": 0.25, "education": 0.20, "keyword": 0.15}

EDUCATION_LEVELS = {
    "phd": 4, "ph.d": 4, "doctorate": 4,
    "master": 3, "masters": 3, "msc": 3, "mca": 3, "mba": 3, "m.tech": 3, "m.e": 3,
    "bachelor": 2, "bachelors": 2, "bsc": 2, "bca": 2, "btech": 2, "b.tech": 2, "b.e": 2, "be": 2,
    "diploma": 1, "certificate": 1,
}

STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","have","has","will","would","can",
    "could","should","may","might","shall","do","does","did","not","this",
    "that","these","those","it","its","we","our","you","your","they","their",
    "as","by","from","up","about","into","through","during","before","after",
    "above","below","between","out","off","over","under","again","further",
}

def calculate_ats_score(resume_text, job_description, skills_data):
    sub = {
        "skill_match": _skill_match(skills_data),
        "experience":  _experience(resume_text, job_description),
        "education":   _education(resume_text, job_description),
        "keyword":     _keyword(resume_text, job_description),
    }
    total = round(sum(sub[k] * WEIGHTS[k] for k in sub))
    total = max(0, min(100, total))
    return {
        "total_score": total,
        "sub_scores":  sub,
        "grade":       _grade(total),
        "feedback":    _feedback(sub, total),
    }

def _skill_match(skills_data):
    jd_skills = len(skills_data.get("jd_skills", []) or [])
    matched   = len(skills_data.get("matched_skills", []) or [])
    if jd_skills == 0:
        return 50
    return max(0, min(100, int(matched / jd_skills * 100)))

def _experience(resume_text, job_description):
    resume_years = _extract_years(resume_text)
    required     = _extract_required_years(job_description)
    if required == 0:
        return 70 if resume_years > 0 else 50
    if resume_years == 0:
        return 40
    ratio = resume_years / required
    if ratio >= 1.5: return 100
    if ratio >= 1.0: return 90
    if ratio >= 0.8: return 75
    if ratio >= 0.5: return 60
    return 40

def _extract_years(text):
    text = text.lower()
    # Match date ranges like 2020-2023, 2021 - present
    patterns = [
        r'(\d{4})\s*[-–—to]+\s*(present|current|now|\d{4})',
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
    ]
    total = 0
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            try:
                start = int(m.group(1))
                end_raw = m.group(2).lower()
                if end_raw in ("present", "current", "now"):
                    end = 2025
                else:
                    end = int(end_raw)
                if 1990 <= start <= 2025 and end >= start:
                    total += (end - start)
            except:
                try:
                    total += int(m.group(1))
                except:
                    pass
    return min(total, 30)

def _extract_required_years(jd):
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'minimum\s*(\d+)\s*years?',
        r'at least\s*(\d+)\s*years?',
        r'(\d+)\s*[-–]\s*(\d+)\s*years?',
    ]
    for pat in patterns:
        m = re.search(pat, jd, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    return 0

def _education(resume_text, job_description):
    resume_lvl = _detect_education(resume_text)
    required   = _detect_education(job_description)
    if required == 0:
        return 80
    if resume_lvl >= required:
        return 100
    diff = required - resume_lvl
    if diff == 1: return 65
    if diff == 2: return 40
    return 25

def _detect_education(text):
    text_lower = text.lower()
    best = 0
    for kw, lvl in EDUCATION_LEVELS.items():
        if kw in text_lower:
            best = max(best, lvl)
    return best

def _keyword(resume_text, job_description):
    r_tokens = _tokenize(resume_text)
    j_tokens = _tokenize(job_description)
    if not j_tokens:
        return 50
    # Unigram overlap
    r_uni = set(r_tokens)
    j_uni = set(j_tokens)
    uni_score = len(r_uni & j_uni) / max(len(j_uni), 1) * 100

    # Bigram overlap
    r_bi = set(zip(r_tokens, r_tokens[1:]))
    j_bi = set(zip(j_tokens, j_tokens[1:]))
    if j_bi:
        bi_score = len(r_bi & j_bi) / max(len(j_bi), 1) * 100
    else:
        bi_score = uni_score

    return max(0, min(100, int(0.6 * uni_score + 0.4 * bi_score)))

def _tokenize(text):
    tokens = re.findall(r'\b[a-z][a-z0-9+#.]*\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def _grade(score):
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    return "D"

def _feedback(sub, total):
    msgs = []
    if sub["skill_match"] < 50:
        msgs.append("Your skill set has significant gaps for this role. Focus on adding the missing skills.")
    elif sub["skill_match"] < 75:
        msgs.append("Moderate skill match. Add more job-specific skills to improve your score.")
    else:
        msgs.append("Strong skill alignment with the job requirements.")

    if sub["keyword"] < 50:
        msgs.append("Low keyword optimisation. Mirror the language used in the job description.")

    if total >= 80:
        msgs.append("Excellent match! You are a strong candidate for this role.")
    elif total >= 65:
        msgs.append("Good match. Minor improvements will make your profile stand out.")
    elif total >= 50:
        msgs.append("Moderate match. Tailor your resume more closely to the job description.")
    else:
        msgs.append("Significant gaps detected. Consider upskilling or targeting a better-matched role.")

    return msgs
