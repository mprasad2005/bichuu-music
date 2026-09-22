import sqlite3
from pathlib import Path
from config import DATABASE_URL

DB_PATH = Path(DATABASE_URL)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS settings (
        chat_id INTEGER PRIMARY KEY,
        volume INTEGER DEFAULT 100,
        admin_only INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL DEFAULT 0,
        name TEXT NOT NULL,
        query TEXT NOT NULL,
        UNIQUE(chat_id, user_id, name, query)
    );
    CREATE TABLE IF NOT EXISTS authorized_users (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY(chat_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS stats (
        chat_id INTEGER PRIMARY KEY,
        plays INTEGER DEFAULT 0,
        skips INTEGER DEFAULT 0
    );
    ''')
    columns = {row[1] for row in cur.execute("PRAGMA table_info(playlists)")}
    if "user_id" not in columns:
        cur.execute("ALTER TABLE playlists ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    table_sql = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='playlists'"
    ).fetchone()[0]
    if "UNIQUE(chat_id, name, query)" in table_sql:
        cur.execute("""
            CREATE TABLE playlists_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL DEFAULT 0,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                UNIQUE(chat_id, user_id, name, query)
            )
        """)
        cur.execute(
            "INSERT INTO playlists_v2(id,chat_id,user_id,name,query) "
            "SELECT id,chat_id,user_id,name,query FROM playlists"
        )
        cur.execute("DROP TABLE playlists")
        cur.execute("ALTER TABLE playlists_v2 RENAME TO playlists")
    con.commit()
    con.close()

def get_settings(chat_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO settings(chat_id) VALUES (?)", (chat_id,))
    con.commit()
    cur.execute("SELECT volume, admin_only FROM settings WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    con.close()
    return {"volume": row[0], "admin_only": bool(row[1])}

def set_volume(chat_id, volume):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR IGNORE INTO settings(chat_id) VALUES (?)", (chat_id,))
    con.execute("UPDATE settings SET volume=? WHERE chat_id=?", (volume, chat_id))
    con.commit()
    con.close()

def set_admin_only(chat_id, enabled):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR IGNORE INTO settings(chat_id) VALUES (?)", (chat_id,))
    con.execute("UPDATE settings SET admin_only=? WHERE chat_id=?", (int(enabled), chat_id))
    con.commit()
    con.close()

def add_playlist(chat_id, user_id, name, query):
    con = sqlite3.connect(DB_PATH)
    cursor = con.execute(
        "INSERT OR IGNORE INTO playlists(chat_id,user_id,name,query) VALUES (?,?,?,?)",
        (chat_id, user_id, name, query),
    )
    con.commit()
    con.close()
    return cursor.rowcount > 0

def remove_playlist(chat_id, user_id, name, query):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "DELETE FROM playlists WHERE chat_id=? AND user_id=? AND name=? AND query=?",
        (chat_id, user_id, name, query),
    )
    con.commit()
    con.close()

def list_playlist(chat_id, user_id, name):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT query FROM playlists WHERE chat_id=? AND user_id=? AND name=? ORDER BY id",
        (chat_id, user_id, name),
    )
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows

def list_playlist_names(chat_id, user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT DISTINCT name FROM playlists WHERE chat_id=? AND user_id=? ORDER BY name",
        (chat_id, user_id),
    )
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows

def authorize_user(chat_id, user_id):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR IGNORE INTO authorized_users(chat_id,user_id) VALUES (?,?)",
        (chat_id, user_id),
    )
    con.commit()
    con.close()

def unauthorize_user(chat_id, user_id):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "DELETE FROM authorized_users WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    con.commit()
    con.close()

def is_authorized(chat_id, user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM authorized_users WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    result = cur.fetchone() is not None
    con.close()
    return result

def add_stat(chat_id, field):
    if field not in ("plays", "skips"):
        return
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR IGNORE INTO stats(chat_id) VALUES (?)", (chat_id,))
    con.execute(f"UPDATE stats SET {field}={field}+1 WHERE chat_id=?", (chat_id,))
    con.commit()
    con.close()

def get_stats(chat_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT plays, skips FROM stats WHERE chat_id=?", (chat_id,))
    row = cur.fetchone() or (0, 0)
    con.close()
    return {"plays": row[0], "skips": row[1]}
