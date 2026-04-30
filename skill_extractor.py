"""
skill_extractor.py - NLP-Based Skill Extraction & Comparison
Uses spaCy to extract skills from resume and job description text,
then compares them to detect matches and gaps.
"""

import re
import spacy
from typing import List, Dict, Set

# ── Load spaCy model (lazy, once per session) ─────────────────────────────────
_NLP = None


def _get_nlp():
    """Load and cache spaCy English model."""
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback: blank model if en_core_web_sm not installed
            print("[skill_extractor] en_core_web_sm not found, using blank model.")
            _NLP = spacy.blank("en")
    return _NLP


# ── Curated technical & soft skill vocabulary ─────────────────────────────────
TECH_SKILLS: Set[str] = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
    "ruby", "php", "swift", "kotlin", "scala", "rust", "r", "matlab", "perl",
    "bash", "shell scripting", "powershell",
    # Web / frontend
    "html", "css", "react", "reactjs", "angular", "angularjs", "vue", "vuejs",
    "next.js", "nuxt.js", "svelte", "tailwind css", "bootstrap", "sass", "less",
    # Backend / frameworks
    "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring",
    "spring boot", "laravel", "rails", "ruby on rails", "asp.net", ".net core",
    # Databases
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "oracle", "ms sql", "mariadb", "neo4j",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
    "ci/cd", "terraform", "ansible", "helm", "linux", "unix", "git", "github",
    "gitlab", "bitbucket", "jira", "confluence",
    # Data & ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "spark", "hadoop", "tableau",
    "power bi", "looker", "data analysis", "data engineering", "etl", "airflow",
    # APIs & others
    "rest api", "graphql", "grpc", "microservices", "agile", "scrum", "kanban",
    "devops", "sre", "cybersecurity", "blockchain", "iot", "embedded systems",
    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",
}

SOFT_SKILLS: Set[str] = {
    "communication", "teamwork", "leadership", "problem solving", "problem-solving",
    "critical thinking", "creativity", "adaptability", "time management",
    "project management", "collaboration", "attention to detail", "multitasking",
    "analytical skills", "analytical thinking", "decision making", "decision-making",
    "negotiation", "presentation skills", "writing skills", "mentoring", "coaching",
    "customer service", "stakeholder management", "cross-functional",
}

ALL_SKILLS = TECH_SKILLS | SOFT_SKILLS


# ── Skill extraction ──────────────────────────────────────────────────────────
def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract a deduplicated list of skills from text using:
    1. Curated vocabulary matching (case-insensitive)
    2. spaCy NER / noun-chunk extraction for unknown terms
    """
    if not text:
        return []

    text_lower = text.lower()
    found: Set[str] = set()

    # ── Pass 1: Vocabulary matching ──
    for skill in ALL_SKILLS:
        # Use word-boundary regex to avoid partial matches
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill.title() if len(skill) > 3 else skill.upper())

    # ── Pass 2: spaCy noun-chunks (catch project/company-specific terms) ──
    try:
        nlp = _get_nlp()
        doc = nlp(text[:50_000])  # limit to avoid slow processing on huge texts
        for chunk in doc.noun_chunks:
            token_text = chunk.text.strip().lower()
            # Keep only plausible multi-word tech terms (2-4 words, no stopwords)
            words = token_text.split()
            if 2 <= len(words) <= 4:
                if not all(t in nlp.Defaults.stop_words for t in words):
                    # Accept if it looks like a technical phrase
                    if _is_likely_skill(token_text):
                        found.add(chunk.text.strip().title())

        # Also extract single-token nouns that look technical
        for token in doc:
            if token.pos_ == "NOUN" and len(token.text) > 3:
                tok_lower = token.text.lower()
                if _is_likely_skill(tok_lower) and tok_lower not in {"work", "team", "year",
                                                                       "role", "company", "project",
                                                                       "experience", "background"}:
                    found.add(token.text.strip().title())
    except Exception:
        pass  # NLP errors shouldn't crash the app

    return sorted(found)


def _is_likely_skill(text: str) -> bool:
    """Heuristic: is a noun phrase likely to be a technical skill?"""
    tech_indicators = [
        "api", "sdk", "framework", "platform", "tool", "language",
        "database", "cloud", "service", "system", "library", "engine",
        "protocol", "architecture", "stack", "pipeline", "workflow",
    ]
    return any(ind in text for ind in tech_indicators)


# ── Comparison ────────────────────────────────────────────────────────────────
def compare_skills(resume_skills: List[str], jd_skills: List[str]) -> Dict:
    """
    Compare resume skills against job-description skills.

    Returns
    -------
    dict with keys:
        matched_skills  – skills present in both
        missing_skills  – skills in JD but not in resume
        extra_skills    – skills in resume but not in JD
        match_pct       – percentage of JD skills covered (0-100)
    """
    resume_set = {s.lower() for s in resume_skills}
    jd_set     = {s.lower() for s in jd_skills}

    matched = jd_set & resume_set
    missing = jd_set - resume_set
    extra   = resume_set - jd_set

    match_pct = round(len(matched) / len(jd_set) * 100, 1) if jd_set else 0.0

    # Re-title-case for display
    def _remap(lowercase_set: Set[str], source: List[str]) -> List[str]:
        mapping = {s.lower(): s for s in source}
        return sorted(mapping.get(s, s.title()) for s in lowercase_set)

    all_skills_combined = resume_skills + jd_skills
    return {
        "matched_skills": _remap(matched, all_skills_combined),
        "missing_skills": _remap(missing, jd_skills),
        "extra_skills":   _remap(extra, resume_skills),
        "match_pct":      match_pct,
    }


# ── Combined convenience function ─────────────────────────────────────────────
def extract_skills(resume_text: str, job_description: str) -> Dict:
    """
    Full pipeline: extract skills from both texts, compare them.

    Returns a dict suitable for use throughout the app.
    """
    resume_skills = extract_skills_from_text(resume_text)
    jd_skills     = extract_skills_from_text(job_description)
    comparison    = compare_skills(resume_skills, jd_skills)

    return {
        "resume_skills":  resume_skills,
        "jd_skills":      jd_skills,
        "matched_skills": comparison["matched_skills"],
        "missing_skills": comparison["missing_skills"],
        "extra_skills":   comparison["extra_skills"],
        "match_pct":      comparison["match_pct"],
    }
