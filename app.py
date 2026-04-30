"""
app.py - NexaCV Flask Application - Simple & Working Version
"""
import os, io, json, uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

from auth import register_user, login_user, save_analysis_history, get_analysis_history, delete_analysis_record
from resume_parser import extract_text_from_pdf
from skill_extractor import extract_skills
from ai_analyzer import analyze_resume_with_groq
from ats_score import calculate_ats_score
from report_generator import generate_pdf_report

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexacv-secret-2024")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# ── File-based store ─────────────────────────────────────────
STORE_DIR = Path(__file__).parent / "data" / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

def store_save(aid, data):
    try:
        with open(STORE_DIR / f"{aid}.json", "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[store_save] {e}")

def store_load(aid):
    try:
        p = STORE_DIR / f"{aid}.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    except Exception as e:
        print(f"[store_load] {e}")
    return None

def get_data():
    aid = session.get("analysis_id")
    return store_load(aid) if aid else None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

app.config["SESSION_PERMANENT"] = False

# ── Routes ─────────────────────────────────────────

@app.route("/")
def index():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/home")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        result   = login_user(username, password)
        if result["success"]:
            session.clear()
            session["user_id"]  = result["user_id"]
            session["username"] = username
            return redirect(url_for("upload"))
        error = result["error"]
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        if password != confirm:
            error = "Passwords do not match."
        else:
            result  = register_user(username, email, password)
            success = "Account created! Please sign in." if result["success"] else None
            error   = result.get("error") if not result["success"] else None
    return render_template("register.html", error=error, success=success)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    error = None
    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_desc    = request.form.get("job_description", "").strip()
        if not resume_file or resume_file.filename == "":
            error = "Please upload a PDF resume."
        elif not job_desc:
            error = "Please paste a job description."
        else:
            resume_text = extract_text_from_pdf(resume_file)
            if not resume_text:
                error = "Could not extract text."
            else:
                aid = str(uuid.uuid4())
                store_save(aid, {
                    "resume_text": resume_text,
                    "resume_filename": secure_filename(resume_file.filename),
                    "job_description": job_desc,
                    "skills": {}, "ats": {}, "ai": {}, "done": False,
                })
                session["analysis_id"] = aid
                session["analysis_done"] = False
                return render_template("loading.html", username=session.get("username"))
    return render_template("upload.html", username=session.get("username"), error=error)

@app.route("/run")
@login_required
def run():
    aid = session.get("analysis_id")
    data = store_load(aid)
    try:
        skills_data = extract_skills(data["resume_text"], data["job_description"])
        ats_result  = calculate_ats_score(data["resume_text"], data["job_description"], skills_data)
        ai_analysis = analyze_resume_with_groq(data["resume_text"], data["job_description"])

        data.update({"skills": skills_data, "ats": ats_result, "ai": ai_analysis, "done": True})
        store_save(aid, data)

        session["analysis_done"] = True

        save_analysis_history(
            user_id=session["user_id"],
            resume_filename=data["resume_filename"],
            ats_result=ats_result,
            skills_data=skills_data,
            ai_analysis=ai_analysis,
            job_description=data["job_description"],
        )

        return redirect(url_for("results"))

    except Exception as e:
        return render_template("error.html", error=str(e))

@app.route("/results")
@login_required
def results():
    data = get_data()
    return render_template("results.html",
        username=session.get("username"),
        skills=data.get("skills", {}),
        ats=data.get("ats", {}),
        ai=data.get("ai", {}),
        filename=data.get("resume_filename", "")
    )

# ── IMPORTANT FIX HERE ─────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
