"""
auth.py - NexaCV Authentication and History
Supports both SQLite (local) and PostgreSQL (Render deployment)
"""
import os, json, sqlite3
from datetime import datetime
from pathlib import Path

import bcrypt

# ── Database connection ────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")  # Set on Render
DB_PATH = Path(__file__).parent / "data" / "nexacv.db"

def _use_postgres():
    return DATABASE_URL is not None

def _get_conn():
    if _use_postgres():
        import psycopg2
        import psycopg2.extras
        # Render uses postgres:// but psycopg2 needs postgresql://
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url)
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(DB_PATH))

def _ph(n):
    """Return placeholder: %s for postgres, ? for sqlite"""
    return "%s" if _use_postgres() else "?"

def init_db():
    """Create tables if they don't exist"""
    conn = _get_conn()
    cur  = conn.cursor()
    if _use_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         SERIAL PRIMARY KEY,
                username   TEXT NOT NULL UNIQUE,
                email      TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id              SERIAL PRIMARY KEY,
                user_id         INTEGER NOT NULL REFERENCES users(id),
                resume_filename TEXT,
                job_description TEXT,
                ats_score       INTEGER,
                grade           TEXT,
                matched_skills  INTEGER,
                missing_skills  INTEGER,
                ai_strengths    TEXT,
                ai_weaknesses   TEXT,
                ai_keywords     TEXT,
                ai_suggestions  TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT NOT NULL UNIQUE,
                email      TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                resume_filename TEXT,
                job_description TEXT,
                ats_score       INTEGER,
                grade           TEXT,
                matched_skills  INTEGER,
                missing_skills  INTEGER,
                ai_strengths    TEXT,
                ai_weaknesses   TEXT,
                ai_keywords     TEXT,
                ai_suggestions  TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()

# Initialize on import
try:
    init_db()
except Exception as e:
    print(f"[auth] DB init error: {e}")

# ── Auth functions ─────────────────────────────────────────────────────────────
def register_user(username, email, password):
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters."}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}
    if "@" not in email:
        return {"success": False, "error": "Please enter a valid email."}
    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        ph = _ph(1)
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            f"INSERT INTO users (username, email, password) VALUES ({ph},{ph},{ph})",
            (username, email, hashed)
        )
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err:
            if "username" in err:
                return {"success": False, "error": "Username already taken."}
            return {"success": False, "error": "Email already registered."}
        return {"success": False, "error": "Registration failed. Please try again."}

def login_user(username, password):
    try:
        ph = _ph(1)
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(f"SELECT id, password FROM users WHERE username={ph}", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return {"success": False, "error": "Invalid username or password."}
        uid, hashed = row
        if bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
            return {"success": True, "user_id": uid}
        return {"success": False, "error": "Invalid username or password."}
    except Exception as e:
        print(f"[login_user] {e}")
        return {"success": False, "error": "Login failed. Please try again."}

def save_analysis_history(user_id, resume_filename, ats_result, skills_data, ai_analysis, job_description=""):
    try:
        ph = _ph(1)
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(f"""
            INSERT INTO analysis_history
            (user_id, resume_filename, job_description, ats_score, grade,
             matched_skills, missing_skills, ai_strengths, ai_weaknesses,
             ai_keywords, ai_suggestions)
            VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
        """, (
            user_id,
            resume_filename,
            (job_description or "")[:500],
            int(ats_result.get("total_score", 0) or 0),
            str(ats_result.get("grade", "—") or "—"),
            len(skills_data.get("matched_skills", []) or []),
            len(skills_data.get("missing_skills", []) or []),
            json.dumps(ai_analysis.get("strengths", []) or []),
            json.dumps(ai_analysis.get("weaknesses", []) or []),
            json.dumps(ai_analysis.get("keywords", []) or []),
            json.dumps(ai_analysis.get("suggestions", []) or []),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[save_analysis_history] {e}")

def get_analysis_history(user_id):
    try:
        ph = _ph(1)
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(f"""
            SELECT id, resume_filename, job_description, ats_score, grade,
                   matched_skills, missing_skills, ai_strengths, ai_weaknesses,
                   ai_keywords, ai_suggestions, created_at
            FROM analysis_history
            WHERE user_id={ph}
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        records = []
        for r in rows:
            records.append({
                "id":              r[0],
                "resume_filename": r[1],
                "job_description": r[2],
                "ats_score":       r[3],
                "grade":           r[4],
                "matched_skills":  r[5],
                "missing_skills":  r[6],
                "ai_strengths":    _safe_json(r[7]),
                "ai_weaknesses":   _safe_json(r[8]),
                "ai_keywords":     _safe_json(r[9]),
                "ai_suggestions":  _safe_json(r[10]),
                "created_at":      str(r[11]),
            })
        return records
    except Exception as e:
        print(f"[get_analysis_history] {e}")
        return []

def delete_analysis_record(record_id, user_id):
    try:
        ph = _ph(1)
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            f"DELETE FROM analysis_history WHERE id={ph} AND user_id={ph}",
            (record_id, user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[delete_analysis_record] {e}")

def _safe_json(val):
    try:
        return json.loads(val) if val else []
    except:
        return []
