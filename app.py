import os, json, uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

from auth import register_user, login_user, save_analysis_history
from resume_parser import extract_text_from_pdf
from skill_extractor import extract_skills
from ai_analyzer import analyze_resume_with_groq
from ats_score import calculate_ats_score

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexacv-secret-2024")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# ---------- ERROR HANDLER (VERY IMPORTANT) ----------
@app.errorhandler(Exception)
def handle_error(e):
    return f"<h2>ERROR:</h2><pre>{str(e)}</pre>", 500


# ---------- STORAGE ----------
STORE_DIR = Path(__file__).parent / "data" / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

def store_save(aid, data):
    try:
        with open(STORE_DIR / f"{aid}.json", "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("[STORE SAVE ERROR]", e)

def store_load(aid):
    try:
        p = STORE_DIR / f"{aid}.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    except Exception as e:
        print("[STORE LOAD ERROR]", e)
    return None

def get_data():
    aid = session.get("analysis_id")
    return store_load(aid) if aid else None


# ---------- AUTH ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------- ROUTES ----------
@app.route("/")
def index():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/home")
def landing():
    return render_template("landing.html")


# ---------- LOGIN (EMAIL BASED) ----------
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


# ---------- REGISTER ----------
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


# ---------- UPLOAD ----------
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    error = None

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_desc = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a PDF resume."
        elif not job_desc:
            error = "Please add a job description."
        else:
            try:
                text = extract_text_from_pdf(resume_file)

                if not text:
                    error = "Could not extract text from PDF."
                else:
                    aid = str(uuid.uuid4())

                    store_save(aid, {
                        "resume_text": text,
                        "resume_filename": secure_filename(resume_file.filename),
                        "job_description": job_desc,
                        "skills": {}, "ats": {}, "ai": {}, "done": False,
                    })

                    session["analysis_id"] = aid

                    return redirect(url_for("run"))

            except Exception as e:
                return f"<h1>UPLOAD ERROR:</h1><pre>{str(e)}</pre>"

    return render_template("upload.html", username=session.get("username"), error=error)


# ---------- RUN ----------
@app.route("/run")
@login_required
def run():
    try:
        aid = session.get("analysis_id")

        if not aid:
            return "ERROR: No analysis_id in session"

        data = store_load(aid)

        if not data:
            return "ERROR: No stored data found"

        skills = extract_skills(data["resume_text"], data["job_description"])
        ats    = calculate_ats_score(data["resume_text"], data["job_description"], skills)
        ai     = analyze_resume_with_groq(data["resume_text"], data["job_description"])

        data.update({
            "skills": skills,
            "ats": ats,
            "ai": ai,
            "done": True
        })

        store_save(aid, data)

        save_analysis_history(
            user_id=session["user_id"],
            resume_filename=data["resume_filename"],
            ats_result=ats,
            skills_data=skills,
            ai_analysis=ai,
            job_description=data["job_description"],
        )

        return redirect(url_for("results"))

    except Exception as e:
        return f"<h1>RUN ERROR:</h1><pre>{str(e)}</pre>"


# ---------- RESULTS ----------
@app.route("/results")
@login_required
def results():
    data = get_data()

    print("DEBUG DATA:", data)

    if not data:
        return "<h1>No data found. Please upload again.</h1>"

    return render_template(
        "results.html",
        username=session.get("username"),
        skills=data.get("skills", {}),
        ats=data.get("ats", {}),
        ai=data.get("ai", {}),
        filename=data.get("resume_filename", "")
    )


# ---------- START ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
