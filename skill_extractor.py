"""
skill_extractor.py - NLP Skill Extraction using spaCy
Two-pass: vocabulary matching + noun-chunk detection
"""
import re

# ── Skills vocabulary ──────────────────────────────────────────────────────────
ALL_SKILLS = [
    # Programming languages
    "python","java","javascript","typescript","c++","c#","c","ruby","go","rust",
    "kotlin","swift","php","scala","r","matlab","perl","bash","shell","powershell",
    # Web frameworks
    "react","angular","vue","django","flask","fastapi","spring","nodejs","node.js",
    "express","laravel","rails","asp.net","next.js","nuxt",
    # Data & ML
    "machine learning","deep learning","nlp","natural language processing",
    "computer vision","data science","pandas","numpy","scikit-learn","tensorflow",
    "pytorch","keras","matplotlib","seaborn","plotly","scipy","statsmodels",
    "xgboost","lightgbm","hugging face","transformers",
    # Databases
    "sql","mysql","postgresql","sqlite","mongodb","redis","cassandra","elasticsearch",
    "dynamodb","oracle","mssql","firebase","supabase",
    # Cloud & DevOps
    "aws","azure","gcp","google cloud","docker","kubernetes","terraform","ansible",
    "jenkins","github actions","ci/cd","linux","git","github","gitlab","bitbucket",
    # Data tools
    "power bi","tableau","excel","spark","hadoop","kafka","airflow","dbt",
    "snowflake","bigquery","redshift","looker",
    # Other tech
    "rest api","graphql","microservices","agile","scrum","jira","postman",
    "selenium","junit","pytest","html","css","bootstrap","tailwind",
    "figma","photoshop","illustrator","android","ios","flutter","react native",
    # Soft skills
    "communication","teamwork","problem solving","leadership","analytical",
    "critical thinking","project management","time management",
]

def extract_skills(resume_text, job_description):
    """Compare skills between resume and job description."""
    resume_skills = _extract(resume_text)
    jd_skills     = _extract(job_description)

    resume_lower = {s.lower() for s in resume_skills}
    jd_lower     = {s.lower() for s in jd_skills}

    matched = sorted({s for s in jd_lower if s in resume_lower})
    missing = sorted({s for s in jd_lower if s not in resume_lower})
    extra   = sorted({s for s in resume_lower if s not in jd_lower})

    return {
        "resume_skills":  sorted(resume_skills),
        "jd_skills":      sorted(jd_skills),
        "matched_skills": [_title(s) for s in matched],
        "missing_skills": [_title(s) for s in missing],
        "extra_skills":   [_title(s) for s in extra],
        "match_percent":  int(len(matched) / max(len(jd_lower), 1) * 100),
    }

def _extract(text):
    if not text:
        return set()
    text_lower = text.lower()
    found = set()

    # Pass 1: vocabulary matching
    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.lower())

    # Pass 2: spaCy noun chunks (if available)
    try:
        import spacy
        nlp = _get_nlp()
        if nlp:
            doc = nlp(text[:50000])
            tech_indicators = {
                "api","sdk","framework","library","platform","database","db",
                "service","engine","tool","system","language","stack","pipeline",
                "model","network","algorithm","protocol","server","cloud","cli",
            }
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.strip().lower()
                words = chunk_text.split()
                if 2 <= len(words) <= 4:
                    if any(w in tech_indicators for w in words):
                        if len(chunk_text) > 3:
                            found.add(chunk_text)
    except Exception as e:
        print(f"[skill_extractor spaCy] {e}")

    return found

_nlp_model = None

def _get_nlp():
    global _nlp_model
    if _nlp_model is None:
        try:
            import spacy
            _nlp_model = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"[skill_extractor] spaCy model not available: {e}")
            _nlp_model = False
    return _nlp_model if _nlp_model is not False else None

def _title(s):
    upper_words = {"sql","nlp","api","aws","gcp","css","html","sdk","ui","ux","ml","ai","ci","cd","php","ios"}
    parts = s.split()
    result = []
    for p in parts:
        if p in upper_words:
            result.append(p.upper())
        elif len(p) <= 3 and p.isalpha():
            result.append(p.upper())
        else:
            result.append(p.capitalize())
    return " ".join(result)
