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

STORE_DIR = Path(__file__).parent / "data" / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

def store_save(aid, data):
    with open(STORE_DIR / f"{aid}.json", "w") as f:
        json.dump(data, f)

def store_load(aid):
    p = STORE_DIR / f"{aid}.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
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

@app.route("/")
def index():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/home")
def landing():
    return render_template("landing.html")

# -------- LOGIN (EMAIL BASED) --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        result = login_user(email, password)

        if result["success"]:
            session.clear()
            session["user_id"] = result["user_id"]
            session["username"] = result["username"]
            return redirect(url_for("upload"))

        error = result["error"]

    return render_template("login.html", error=error)

# -------- REGISTER --------
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
            result = register_user(username, email, password)
            if result["success"]:
                success = "Account created! Please sign in."
            else:
                error = result.get("error")

    return render_template("register.html", error=error, success=success)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------- UPLOAD --------
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    error = None

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_desc = request.form.get("job_description", "").strip()

        if not resume_file:
            error = "Upload a PDF."
        elif not job_desc:
            error = "Add job description."
        else:
            text = extract_text_from_pdf(resume_file)

            aid = str(uuid.uuid4())

            store_save(aid, {
                "resume_text": text,
                "resume_filename": secure_filename(resume_file.filename),
                "job_description": job_desc,
                "skills": {}, "ats": {}, "ai": {}, "done": False,
            })

            session["analysis_id"] = aid

            return redirect(url_for("run"))

    return render_template("upload.html", username=session.get("username"), error=error)

# -------- RUN --------
@app.route("/run")
@login_required
def run():
    aid = session.get("analysis_id")

    if not aid:
        return redirect(url_for("upload"))

    data = store_load(aid)

    if not data:
        return redirect(url_for("upload"))

    skills = extract_skills(data["resume_text"], data["job_description"])
    ats    = calculate_ats_score(data["resume_text"], data["job_description"], skills)
    ai     = analyze_resume_with_groq(data["resume_text"], data["job_description"])

    data.update({"skills": skills, "ats": ats, "ai": ai, "done": True})
    store_save(aid, data)

    return redirect(url_for("results"))

# -------- RESULTS --------
@app.route("/results")
@login_required
def results():
    data = get_data()

    if not data:
        return redirect(url_for("upload"))

    return render_template("results.html",
        username=session.get("username"),
        skills=data.get("skills"),
        ats=data.get("ats"),
        ai=data.get("ai"),
        filename=data.get("resume_filename")
    )

# -------- RUN FOR RENDER --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
