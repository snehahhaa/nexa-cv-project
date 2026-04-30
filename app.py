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

# ── File-based store so data survives server restarts ─────────────────────────
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

# ── Session config — clears on every server restart ───────────────────────────
app.config["SESSION_PERMANENT"] = False

# ── Auth ───────────────────────────────────────────────────────────────────────
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

# ── Upload ─────────────────────────────────────────────────────────────────────
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
                error = "Could not extract text. Make sure the PDF is not scanned."
            else:
                aid = str(uuid.uuid4())
                store_save(aid, {
                    "resume_text":     resume_text,
                    "resume_filename": secure_filename(resume_file.filename),
                    "job_description": job_desc,
                    "skills": {}, "ats": {}, "ai": {}, "done": False,
                })
                session["analysis_id"]   = aid
                session["analysis_done"] = False
                # Show loading page which auto-redirects to /run
                return render_template("loading.html", username=session.get("username"))
    return render_template("upload.html", username=session.get("username"), error=error)

# ── Run Analysis (called from loading page) ────────────────────────────────────
@app.route("/run")
@login_required
def run():
    aid = session.get("analysis_id")
    if not aid:
        return redirect(url_for("upload"))
    data = store_load(aid)
    if not data:
        return redirect(url_for("upload"))
    try:
        print("\n[run] Step 1: Extracting skills...")
        skills_data = extract_skills(data["resume_text"], data["job_description"])
        print("[run] Step 2: Calculating ATS score...")
        ats_result  = calculate_ats_score(data["resume_text"], data["job_description"], skills_data)
        print("[run] Step 3: Running Groq AI...")
        ai_analysis = analyze_resume_with_groq(data["resume_text"], data["job_description"])
        print("[run] Step 4: Saving results...")
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
        print("[run] Done! Redirecting to results.")
        return redirect(url_for("results"))
    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template("error.html", username=session.get("username"), error=str(e))

# ── Results ────────────────────────────────────────────────────────────────────
@app.route("/results")
@login_required
def results():
    data = get_data()
    if not data or not data.get("done"):
        return render_template("no_analysis.html", username=session.get("username"))
    return render_template("results.html",
        username=session.get("username"),
        skills=data.get("skills", {}),
        ats=data.get("ats", {}),
        ai=data.get("ai", {}),
        filename=data.get("resume_filename", ""))

# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    data = get_data()
    if not data or not data.get("done"):
        return render_template("no_analysis.html", username=session.get("username"))
    return render_template("dashboard.html",
        username=session.get("username"),
        skills=data.get("skills", {}),
        ats=data.get("ats", {}))

# ── History ────────────────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    records = get_analysis_history(session["user_id"])
    return render_template("history.html", username=session.get("username"), records=records)

@app.route("/delete-history/<int:record_id>", methods=["POST"])
@login_required
def delete_history(record_id):
    delete_analysis_record(record_id, session["user_id"])
    return redirect(url_for("history"))

# ── Download ───────────────────────────────────────────────────────────────────
@app.route("/download-report")
@login_required
def download_report():
    data = get_data()
    if not data or not data.get("done"):
        return render_template("no_analysis.html", username=session.get("username"))
    pdf_bytes = generate_pdf_report(
        username=session.get("username", ""),
        resume_filename=data.get("resume_filename", ""),
        ats_result=data.get("ats", {}),
        skills_data=data.get("skills", {}),
        ai_analysis=data.get("ai", {}),
    )
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"nexacv_{session.get('username','user')}.pdf")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
