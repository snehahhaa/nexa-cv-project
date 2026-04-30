"""
ats_score.py - ATS Compatibility Score Calculator
Computes a 0-100 ATS score from four weighted sub-scores:
  - Skill match score      (40%)
  - Experience relevance   (25%)
  - Education match        (20%)
  - Keyword optimisation   (15%)
"""

import re
from typing import Dict, List


# ── Sub-score weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    "skill_match": 0.40,
    "experience":  0.25,
    "education":   0.20,
    "keyword":     0.15,
}

# ── Education keyword maps ────────────────────────────────────────────────────
EDUCATION_KEYWORDS = {
    "phd":          ["phd", "doctorate", "doctoral", "ph.d"],
    "masters":      ["master", "m.s.", "msc", "mba", "m.tech", "m.e."],
    "bachelors":    ["bachelor", "b.s.", "bsc", "b.tech", "b.e.", "b.a.", "undergraduate"],
    "diploma":      ["diploma", "associate", "certificate"],
}

EXPERIENCE_INDICATORS = [
    r"\b(\d+)\+?\s+years?\s+(of\s+)?(experience|exp)\b",
    r"\b(experience|exp)\s+of\s+(\d+)\+?\s+years?\b",
    r"\b(\d{4})\s*[-–]\s*(\d{4}|present|current)\b",  # date ranges
]

SENIOR_WORDS  = ["senior", "lead", "principal", "staff", "architect", "manager", "director", "head"]
JUNIOR_WORDS  = ["junior", "entry", "intern", "trainee", "associate", "graduate"]


# ── Public API ────────────────────────────────────────────────────────────────
def calculate_ats_score(
    resume_text: str,
    job_description: str,
    skills_data: Dict,
) -> Dict:
    """
    Calculate the overall ATS score and individual sub-scores.

    Parameters
    ----------
    resume_text     : plain text of the resume
    job_description : plain text of the job description
    skills_data     : output from skill_extractor.extract_skills()

    Returns
    -------
    dict:
        total_score  – int 0-100
        sub_scores   – dict {skill_match, experience, education, keyword}
        grade        – str  "A" / "B" / "C" / "D"
        feedback     – list[str]  brief feedback messages
    """
    sub = {
        "skill_match": _skill_match_score(skills_data),
        "experience":  _experience_score(resume_text, job_description),
        "education":   _education_score(resume_text, job_description),
        "keyword":     _keyword_score(resume_text, job_description),
    }

    total = round(sum(sub[k] * WEIGHTS[k] for k in sub))
    total = max(0, min(100, total))  # clamp to 0-100

    return {
        "total_score": total,
        "sub_scores":  sub,
        "grade":       _grade(total),
        "feedback":    _feedback(sub, total),
    }


# ── Sub-score calculators ─────────────────────────────────────────────────────
def _skill_match_score(skills_data: Dict) -> int:
    """Score based on ratio of matched skills to total JD skills."""
    jd_total    = len(skills_data.get("jd_skills", []))
    matched     = len(skills_data.get("matched_skills", []))

    if jd_total == 0:
        return 50  # neutral when JD has no detectable skills
    ratio = matched / jd_total
    score = int(ratio * 100)
    return max(0, min(100, score))


def _experience_score(resume_text: str, jd_text: str) -> int:
    """
    Score experience relevance by comparing seniority signals and
    years of experience mentioned in JD vs resume.
    """
    resume_lower = resume_text.lower()
    jd_lower     = jd_text.lower()

    # Extract years from JD requirement
    jd_years    = _extract_years_required(jd_lower)
    resume_years = _extract_total_years(resume_lower)

    if jd_years is None:
        year_score = 70  # no explicit requirement → neutral
    elif resume_years is None:
        year_score = 40
    elif resume_years >= jd_years:
        year_score = 100
    else:
        # Partial credit
        year_score = int((resume_years / jd_years) * 100)

    # Seniority alignment
    jd_senior    = any(w in jd_lower    for w in SENIOR_WORDS)
    jd_junior    = any(w in jd_lower    for w in JUNIOR_WORDS)
    res_senior   = any(w in resume_lower for w in SENIOR_WORDS)
    res_junior   = any(w in resume_lower for w in JUNIOR_WORDS)

    if jd_senior and res_senior:
        seniority_bonus = 10
    elif jd_junior and (res_junior or not res_senior):
        seniority_bonus = 10
    elif jd_senior and not res_senior:
        seniority_bonus = -10
    else:
        seniority_bonus = 0

    score = max(0, min(100, year_score + seniority_bonus))
    return score


def _education_score(resume_text: str, jd_text: str) -> int:
    """
    Match education level in resume against requirements in JD.
    """
    resume_lower = resume_text.lower()
    jd_lower     = jd_text.lower()

    resume_level = _detect_education_level(resume_lower)
    jd_level     = _detect_education_level(jd_lower)

    LEVEL_RANK = {"phd": 4, "masters": 3, "bachelors": 2, "diploma": 1, None: 0}

    resume_rank = LEVEL_RANK.get(resume_level, 0)
    jd_rank     = LEVEL_RANK.get(jd_level, 0)

    if jd_rank == 0:
        return 75   # no education requirement → mostly neutral
    if resume_rank >= jd_rank:
        return 100
    if resume_rank == jd_rank - 1:
        return 65   # one level below
    return 30       # significantly below


def _keyword_score(resume_text: str, jd_text: str) -> int:
    """
    Calculate how well the resume's keywords match the JD's important terms.
    Extracts meaningful n-grams and checks overlap.
    """
    resume_words = _tokenise(resume_text)
    jd_words     = _tokenise(jd_text)

    # Unigrams
    jd_unique  = set(jd_words)
    overlap    = jd_unique & set(resume_words)

    # Bigrams
    jd_bigrams  = set(_ngrams(jd_words,  2))
    res_bigrams = set(_ngrams(resume_words, 2))
    bigram_overlap = jd_bigrams & res_bigrams

    uni_score    = (len(overlap)        / len(jd_unique)  * 100) if jd_unique  else 50
    bi_score     = (len(bigram_overlap) / len(jd_bigrams) * 100) if jd_bigrams else 50

    # Weighted blend: unigrams 60%, bigrams 40%
    score = 0.6 * uni_score + 0.4 * bi_score
    return max(0, min(100, int(score)))


# ── Helpers ───────────────────────────────────────────────────────────────────
def _extract_years_required(text: str):
    """Extract the number of years required from JD text."""
    patterns = [
        r"(\d+)\+?\s+years?\s+(of\s+)?(experience|exp)",
        r"minimum\s+(\d+)\s+years?",
        r"at\s+least\s+(\d+)\s+years?",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return int(m.group(1))
    return None


def _extract_total_years(resume_text: str):
    """
    Estimate total years of experience from date ranges in resume.
    Returns None if no date ranges found.
    """
    date_range_pattern = r"(\d{4})\s*[-–]\s*(\d{4}|present|current|now)"
    matches = re.findall(date_range_pattern, resume_text, re.IGNORECASE)
    if not matches:
        return None

    total = 0
    import datetime
    current_year = datetime.datetime.now().year
    for start, end in matches:
        try:
            s = int(start)
            e = current_year if end.lower() in ("present", "current", "now") else int(end)
            if 1970 <= s <= current_year and s <= e:
                total += e - s
        except ValueError:
            pass
    return total if total > 0 else None


def _detect_education_level(text: str):
    """Return the highest education level found in text."""
    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level
    return None


def _tokenise(text: str) -> List[str]:
    """Lower-case, remove punctuation, tokenise, remove stopwords."""
    stop = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
        "of", "with", "is", "are", "was", "were", "be", "been", "will",
        "that", "this", "it", "we", "you", "he", "she", "they",
    }
    words = re.findall(r"\b[a-z][a-z0-9\+#\.]+\b", text.lower())
    return [w for w in words if w not in stop and len(w) > 2]


def _ngrams(tokens: List[str], n: int) -> List[tuple]:
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def _grade(score: int) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    return "D"


def _feedback(sub: Dict, total: int) -> List[str]:
    msgs = []
    if total >= 80:
        msgs.append("Excellent! Your resume is highly compatible with this role.")
    elif total >= 65:
        msgs.append("Good match. A few targeted improvements will make you stand out.")
    elif total >= 50:
        msgs.append("Moderate match. Consider tailoring your resume more closely to the job.")
    else:
        msgs.append("Low match. Significant gaps exist between your profile and the role.")

    if sub["skill_match"] < 50:
        msgs.append("Skill coverage is low — add more of the required skills to your resume.")
    if sub["experience"] < 50:
        msgs.append("Experience level may not fully align with the job requirements.")
    if sub["education"] < 65:
        msgs.append("Education requirements may not be fully met.")
    if sub["keyword"] < 50:
        msgs.append("Keyword optimisation is weak — mirror language from the job description.")

    return msgs
