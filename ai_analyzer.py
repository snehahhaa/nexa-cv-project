"""
ai_analyzer.py - Groq AI Integration
Uses LLaMA 3.3 70B via Groq API for resume analysis
"""
import os, json, re
from dotenv import load_dotenv

load_dotenv(override=True)

_MODEL = "llama-3.3-70b-versatile"

def analyze_resume_with_groq(resume_text, job_description):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        print("[ai_analyzer] No GROQ_API_KEY found, using fallback")
        return _fallback()
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = _build_prompt(resume_text, job_description)
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": (
                    "You are an expert ATS analyst and career coach. "
                    "Always respond with valid JSON only. No markdown, no explanation."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content.strip()
        return _parse(raw)
    except Exception as e:
        print(f"[ai_analyzer] Error: {e}")
        return _fallback()

def _build_prompt(resume_text, job_description):
    r = resume_text[:4000] if len(resume_text) > 4000 else resume_text
    j = job_description[:2000] if len(job_description) > 2000 else job_description
    return f"""Analyse this resume against the job description.

RESUME:
{r}

JOB DESCRIPTION:
{j}

Return ONLY a JSON object with exactly these 5 keys:
{{
  "strengths": ["3 to 5 specific strengths of this resume for this role"],
  "weaknesses": ["3 to 5 specific weaknesses or gaps"],
  "missing_skills": ["skills mentioned in JD but absent from resume"],
  "keywords": ["5 to 8 ATS keywords to add to the resume"],
  "suggestions": ["3 to 5 specific actionable improvement suggestions"]
}}

Return ONLY the JSON. No other text."""

def _parse(raw):
    try:
        clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        return json.loads(clean)
    except:
        pass
    result = {"strengths": [], "weaknesses": [], "missing_skills": [], "keywords": [], "suggestions": []}
    patterns = {
        "strengths":      r'"strengths"\s*:\s*\[(.*?)\]',
        "weaknesses":     r'"weaknesses"\s*:\s*\[(.*?)\]',
        "missing_skills": r'"missing_skills"\s*:\s*\[(.*?)\]',
        "keywords":       r'"keywords"\s*:\s*\[(.*?)\]',
        "suggestions":    r'"suggestions"\s*:\s*\[(.*?)\]',
    }
    for key, pat in patterns.items():
        m = re.search(pat, raw, re.DOTALL)
        if m:
            items = re.findall(r'"([^"]+)"', m.group(1))
            result[key] = items
    return result

def _fallback():
    return {
        "strengths":      ["Resume submitted successfully", "Profile reviewed"],
        "weaknesses":     ["AI analysis unavailable at this time"],
        "missing_skills": ["Unable to determine — AI service unavailable"],
        "keywords":       ["Please retry the analysis"],
        "suggestions":    ["Ensure your GROQ_API_KEY is set correctly and retry"],
    }
