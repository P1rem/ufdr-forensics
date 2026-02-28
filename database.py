"""
database.py — SQLite storage for users + analysis history
"""
import sqlite3, json
from datetime import datetime

DB = "ufdrinsight.db"

def init_db():
    con = sqlite3.connect(DB)
    c   = con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created  TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS analyses(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT NOT NULL,
        file_name   TEXT NOT NULL,
        description TEXT,
        analyzed_at TEXT NOT NULL,
        metrics_json TEXT,
        summary     TEXT,
        risks_json  TEXT,
        pdf_bytes   BLOB)""")
    try:
        c.execute("INSERT INTO users(username,password,created) VALUES(?,?,?)",
                  ("admin","admin123",datetime.now().isoformat()))
    except sqlite3.IntegrityError:
        pass
    con.commit(); con.close()

def register_user(username, password):
    if not username or not password:
        return False, "Username and password required."
    if len(password) < 4:
        return False, "Password must be 4+ characters."
    try:
        con = sqlite3.connect(DB)
        con.execute("INSERT INTO users(username,password,created) VALUES(?,?,?)",
                    (username.strip(), password, datetime.now().isoformat()))
        con.commit(); con.close()
        return True, "Account created!"
    except sqlite3.IntegrityError:
        return False, "Username already taken."

def login_user(username, password):
    con = sqlite3.connect(DB)
    row = con.execute("SELECT id FROM users WHERE username=? AND password=?",
                      (username.strip(), password)).fetchone()
    con.close()
    return row is not None

def save_analysis(username, file_name, description, metrics, summary, risks, pdf_bytes):
    con = sqlite3.connect(DB)
    con.execute("""INSERT INTO analyses
        (username,file_name,description,analyzed_at,metrics_json,summary,risks_json,pdf_bytes)
        VALUES(?,?,?,?,?,?,?,?)""",
        (username, file_name, description or "",
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         json.dumps(metrics), summary, json.dumps(risks), pdf_bytes))
    con.commit(); con.close()

def get_history(username):
    con = sqlite3.connect(DB)
    rows = con.execute("""SELECT id,file_name,description,analyzed_at,
        metrics_json,summary,risks_json
        FROM analyses WHERE username=? ORDER BY analyzed_at DESC""",
        (username,)).fetchall()
    con.close()
    out = []
    for r in rows:
        try: metrics = json.loads(r[4]) if r[4] else {}
        except: metrics = {}
        try: risks = json.loads(r[6]) if r[6] else []
        except: risks = []
        out.append({"id":r[0],"file_name":r[1],"description":r[2],
                    "analyzed_at":r[3],"metrics":metrics,"summary":r[5] or "","risks":risks})
    return out

def get_pdf(analysis_id):
    con = sqlite3.connect(DB)
    row = con.execute("SELECT pdf_bytes FROM analyses WHERE id=?",
                      (analysis_id,)).fetchone()
    con.close()
    return row[0] if row and row[0] else b""

def delete_analysis(analysis_id):
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
    con.commit(); con.close()

init_db()
