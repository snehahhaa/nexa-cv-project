"""
auth.py - NexaCV Authentication & History
SQLite + bcrypt user management and analysis history.
"""
import sqlite3, bcrypt, json
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "nexacv.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _create_tables(conn)
    return conn

def _create_tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS analysis_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_filename TEXT, job_description TEXT,
        ats_score INTEGER, grade TEXT,
        matched_skills INTEGER, missing_skills INTEGER,
        ai_strengths TEXT, ai_weaknesses TEXT,
        ai_keywords TEXT, ai_suggestions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")
    conn.commit()

def hash_password(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def register_user(username, email, password):
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters."}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}
    if "@" not in email:
        return {"success": False, "error": "Please enter a valid email address."}
    try:
        conn = get_connection()
        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                     (username, email.lower(), hash_password(password)))
        conn.commit()
        return {"success": True}
    except sqlite3.IntegrityError as e:
        if "username" in str(e): return {"success": False, "error": "Username already taken."}
        if "email"    in str(e): return {"success": False, "error": "Email already registered."}
        return {"success": False, "error": "Registration failed."}
    finally:
        conn.close()

def login_user(username, password):
    try:
        conn = get_connection()
        row  = conn.execute("SELECT id, password FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()
    if not row: return {"success": False, "error": "Invalid username or password."}
    user_id, hashed = row
    if not verify_password(password, hashed): return {"success": False, "error": "Invalid username or password."}
    return {"success": True, "user_id": user_id}

def save_analysis_history(user_id, resume_filename, ats_result, skills_data, ai_analysis, job_description=""):
    try:
        conn = get_connection()
        conn.execute("""INSERT INTO analysis_history
            (user_id, resume_filename, job_description, ats_score, grade,
             matched_skills, missing_skills, ai_strengths, ai_weaknesses, ai_keywords, ai_suggestions)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
            user_id, resume_filename, job_description[:500],
            ats_result.get("total_score", 0), ats_result.get("grade", "-"),
            len(skills_data.get("matched_skills", [])), len(skills_data.get("missing_skills", [])),
            json.dumps(ai_analysis.get("strengths",   [])),
            json.dumps(ai_analysis.get("weaknesses",  [])),
            json.dumps(ai_analysis.get("keywords",    [])),
            json.dumps(ai_analysis.get("suggestions", [])),
        ))
        conn.commit()
    except Exception as e:
        print(f"[auth] save_analysis_history error: {e}")
    finally:
        conn.close()

def get_analysis_history(user_id):
    try:
        conn  = get_connection()
        rows  = conn.execute("""SELECT id, resume_filename, job_description, ats_score, grade,
            matched_skills, missing_skills, ai_strengths, ai_weaknesses,
            ai_keywords, ai_suggestions, created_at
            FROM analysis_history WHERE user_id = ? ORDER BY created_at DESC""", (user_id,)).fetchall()
    except: return []
    finally: conn.close()
    out = []
    for r in rows:
        out.append({"id": r[0], "resume_filename": r[1], "job_description": r[2], "ats_score": r[3],
                    "grade": r[4], "matched_skills": r[5], "missing_skills": r[6],
                    "ai_strengths":  _j(r[7]),  "ai_weaknesses": _j(r[8]),
                    "ai_keywords":   _j(r[9]),  "ai_suggestions": _j(r[10]),
                    "created_at":    r[11]})
    return out

def _j(v):
    try: return json.loads(v) if v else []
    except: return []

def delete_analysis_record(record_id, user_id):
    """Delete a specific analysis record belonging to the user."""
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
