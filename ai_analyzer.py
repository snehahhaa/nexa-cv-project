"""
ai_analyzer.py - Resume Analysis using Groq API (Free & Fast)
Uses Groq's llama-3.3-70b-versatile model — no quota issues on free tier.
"""

import os
import json
import re
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

_MODEL_NAME = "llama-3.3-70b-versatile"   # fast, free, accurate
_PROMPT_DIR = Path(__file__).parent / "prompts"


def _get_client():
    """Create and return a Groq client."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found in .env file.")
    return Groq(api_key=api_key)


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def analyze_resume_with_groq(resume_text: str, job_description: str) -> dict:
    """
    Send resume + JD to Groq LLaMA and return structured analysis.
    (Main analysis function using Groq AI + LLaMA.)

    Returns
    -------
    dict with keys:
        strengths      - list[str]
        weaknesses     - list[str]
        missing_skills - list[str]
        keywords       - list[str]
        suggestions    - list[str]
        raw_response   - str
        error          - str or None
    """
    empty_result = {
        "strengths":      [],
        "weaknesses":     [],
        "missing_skills": [],
        "keywords":       [],
        "suggestions":    [],
        "raw_response":   "",
        "error":          None,
    }

    if not resume_text or not job_description:
        empty_result["error"] = "Resume text or job description is empty."
        return empty_result

    try:
        client = _get_client()
        prompt = _build_analysis_prompt(resume_text, job_description)

        response = client.chat.completions.create(
            model=_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert ATS analyst and career coach. "
                        "Always respond with valid JSON only — no markdown, no extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
            max_tokens=2048,
        )

        raw_text = response.choices[0].message.content.strip()
        parsed   = _parse_response(raw_text)
        parsed["raw_response"] = raw_text
        parsed["error"]        = None
        return parsed

    except EnvironmentError as e:
        empty_result["error"] = str(e)
        return empty_result
    except Exception as e:
        empty_result["error"] = f"Groq API error: {e}"
        empty_result.update(_fallback_analysis())
        return empty_result


def _build_analysis_prompt(resume_text: str, job_description: str) -> str:
    """Construct the analysis prompt."""
    base_prompt      = _load_prompt("analysis_prompt.txt") or (
        "You are an expert ATS analyst and career coach with 15+ years of experience."
    )
    improvement_hint = _load_prompt("improvement_prompt.txt") or (
        "For suggestions, provide specific, actionable improvements the candidate can make."
    )

    resume_snippet = resume_text[:4000]
    jd_snippet     = job_description[:2000]

    return f"""
{base_prompt}
{improvement_hint}

RESUME:
\"\"\"{resume_snippet}\"\"\"

JOB DESCRIPTION:
\"\"\"{jd_snippet}\"\"\"

Respond ONLY with a valid JSON object — no markdown, no extra text, no code fences:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "missing_skills": ["skill 1", "skill 2", "skill 3"],
  "keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"]
}}
Ensure each list has 3-6 specific, concise, actionable items.
""".strip()


def _parse_response(raw: str) -> dict:
    """Parse response into a structured dict. Tries JSON first."""
    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(cleaned)
        return {
            "strengths":      _ensure_list(data.get("strengths",      [])),
            "weaknesses":     _ensure_list(data.get("weaknesses",     [])),
            "missing_skills": _ensure_list(data.get("missing_skills", [])),
            "keywords":       _ensure_list(data.get("keywords",       [])),
            "suggestions":    _ensure_list(data.get("suggestions",    [])),
        }
    except json.JSONDecodeError:
        return _regex_extract(raw)


def _regex_extract(text: str) -> dict:
    """Fallback: extract sections from non-JSON response."""
    sections = {
        "strengths":      r"(?i)strengths?[:\-]*\s*(.*?)(?=weaknesses?|missing|keywords?|suggestions?|$)",
        "weaknesses":     r"(?i)weaknesses?[:\-]*\s*(.*?)(?=strengths?|missing|keywords?|suggestions?|$)",
        "missing_skills": r"(?i)missing\s+skills?[:\-]*\s*(.*?)(?=strengths?|weaknesses?|keywords?|suggestions?|$)",
        "keywords":       r"(?i)keywords?[:\-]*\s*(.*?)(?=strengths?|weaknesses?|missing|suggestions?|$)",
        "suggestions":    r"(?i)suggestions?[:\-]*\s*(.*?)(?=strengths?|weaknesses?|missing|keywords?|$)",
    }
    result = {}
    for key, pattern in sections.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            items = re.findall(r"[-•*]\s*(.+)", match.group(1).strip())
            result[key] = [i.strip() for i in items if i.strip()][:6]
        else:
            result[key] = []
    return result


def _ensure_list(value) -> list:
    """Guarantee the value is a list of strings."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return []


def _fallback_analysis() -> dict:
    """Return generic fallback when API is unavailable."""
    return {
        "strengths": [
            "Resume structure appears professional.",
            "Work experience section is present.",
            "Educational background is mentioned.",
        ],
        "weaknesses": [
            "Could not perform AI analysis — check your GROQ_API_KEY.",
            "Skills section may need expansion.",
        ],
        "missing_skills": ["Unable to determine — Groq API unavailable."],
        "keywords":       ["Please configure GROQ_API_KEY in .env to get recommendations."],
        "suggestions": [
            "Add GROQ_API_KEY to .env to enable AI analysis.",
            "Ensure your resume includes quantified achievements.",
            "Mirror the job description language in your resume.",
        ],
    }
