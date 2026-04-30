import sqlite3
import os
from flask import g, current_app

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'gikipedia.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user',
            avatar    TEXT,
            bio       TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS articles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            slug       TEXT UNIQUE NOT NULL,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL,
            author_id  INTEGER REFERENCES users(id),
            rating     INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            text       TEXT NOT NULL,
            link       TEXT,
            is_read    INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id    INTEGER REFERENCES users(id),
            to_id      INTEGER REFERENCES users(id),
            text       TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS friendships (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id    INTEGER REFERENCES users(id),
            to_id      INTEGER REFERENCES users(id),
            status     TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(from_id, to_id)
        );

        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER REFERENCES users(id),
            target_type TEXT NOT NULL,
            target_id   INTEGER NOT NULL,
            reason      TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'open',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()

    # Migration: add link column if missing
    cols = [row[1] for row in db.execute("PRAGMA table_info(notifications)").fetchall()]
    if 'link' not in cols:
        db.execute("ALTER TABLE notifications ADD COLUMN link TEXT")
    db.commit()

    # Seed test users
    import hashlib
    def pw(plain):
        return hashlib.sha256(plain.encode()).hexdigest()

    users = [
        ('admin',     pw('admin123'),  'admin'),
        ('moderator', pw('moder123'),  'moderator'),
    ]
    for username, password, role in users:
        existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                (username, password, role)
            )
    db.commit()
    db.close()
