
"""
auth.py - NexaCV Authentication & History
SQLite + bcrypt user management and analysis history.
"""
import sqlite3
import bcrypt
import json
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "data" / "nexacv.db"

# ------------------ DB CONNECTION ------------------

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn

def _create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_filename TEXT,
            job_description TEXT,
            ats_score INTEGER,
            grade TEXT,
            matched_skills INTEGER,
            missing_skills INTEGER,
            ai_strengths TEXT,
            ai_weaknesses TEXT,
            ai_keywords TEXT,
            ai_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()

# ------------------ PASSWORD ------------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ------------------ REGISTER ------------------

def register_user(username, email, password):
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters."}

    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}

    if "@" not in email:
        return {"success": False, "error": "Enter a valid email."}

    try:
        conn = get_connection()

        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email.lower(), hash_password(password))
        )

        conn.commit()
        return {"success": True}

    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "error": "Username already exists."}
        if "email" in str(e):
            return {"success": False, "error": "Email already registered."}
        return {"success": False, "error": "Registration failed."}

    finally:
        conn.close()

# ------------------ LOGIN (EMAIL BASED) ------------------

def login_user(email, password):
    try:
        conn = get_connection()

        user = conn.execute(
            "SELECT id, username, password FROM users WHERE email = ?",
            (email.lower(),)
        ).fetchone()

    finally:
        conn.close()

    if not user:
        return {"success": False, "error": "Invalid email or password."}

    if not verify_password(password, user["password"]):
        return {"success": False, "error": "Invalid email or password."}

    return {
        "success": True,
        "user_id": user["id"],
        "username": user["username"]
    }

# ------------------ SAVE HISTORY ------------------

def save_analysis_history(user_id, resume_filename, ats_result, skills_data, ai_analysis, job_description=""):
    try:
        conn = get_connection()

        conn.execute("""
            INSERT INTO analysis_history (
                user_id,
                resume_filename,
                job_description,
                ats_score,
                grade,
                matched_skills,
                missing_skills,
                ai_strengths,
                ai_weaknesses,
                ai_keywords,
                ai_suggestions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            resume_filename,
            job_description[:500],
            ats_result.get("total_score", 0),
            ats_result.get("grade", "-"),
            len(skills_data.get("matched_skills", [])),
            len(skills_data.get("missing_skills", [])),
            json.dumps(ai_analysis.get("strengths", [])),
            json.dumps(ai_analysis.get("weaknesses", [])),
            json.dumps(ai_analysis.get("keywords", [])),
            json.dumps(ai_analysis.get("suggestions", [])),
        ))

        conn.commit()

    except Exception as e:
        print(f"[auth] save_analysis_history error: {e}")

    finally:
        conn.close()

# ------------------ GET HISTORY ------------------

def get_analysis_history(user_id):
    try:
        conn = get_connection()

        rows = conn.execute("""
            SELECT * FROM analysis_history
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()

    except Exception:
        return []

    finally:
        conn.close()

    history = []

    for r in rows:
        history.append({
            "id": r["id"],
            "resume_filename": r["resume_filename"],
            "job_description": r["job_description"],
            "ats_score": r["ats_score"],
            "grade": r["grade"],
            "matched_skills": r["matched_skills"],
            "missing_skills": r["missing_skills"],
            "ai_strengths": json.loads(r["ai_strengths"]) if r["ai_strengths"] else [],
            "ai_weaknesses": json.loads(r["ai_weaknesses"]) if r["ai_weaknesses"] else [],
            "ai_keywords": json.loads(r["ai_keywords"]) if r["ai_keywords"] else [],
            "ai_suggestions": json.loads(r["ai_suggestions"]) if r["ai_suggestions"] else [],
            "created_at": r["created_at"]
        })

    return history

# ------------------ DELETE ------------------

def delete_analysis_record(record_id, user_id):
    try:
        conn = get_connection()

        conn.execute(
            "DELETE FROM analysis_history WHERE id = ? AND user_id = ?",
            (record_id, user_id)
        )

        conn.commit()

    except Exception as e:
        print(f"[auth] delete_analysis_record error: {e}")

    finally:
        conn.close()
```
