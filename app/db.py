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
            friend_code TEXT UNIQUE,  -- Уникальный код для поиска друзей
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS articles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            slug       TEXT UNIQUE NOT NULL,
            title      TEXT NOT NULL,
            description TEXT,  -- Краткое описание статьи
            body       TEXT NOT NULL,
            tag        TEXT,   -- Тег/категория статьи
            cover_image TEXT,  -- URL обложки статьи
            author_id  INTEGER REFERENCES users(id),
            last_editor_id INTEGER REFERENCES users(id),  -- Кто последний редактировал
            rating     INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS article_ratings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            user_id    INTEGER REFERENCES users(id),
            rating     INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(article_id, user_id)
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

    # Migration: add new columns to articles table if missing
    cols = [row[1] for row in db.execute("PRAGMA table_info(articles)").fetchall()]
    if 'description' not in cols:
        db.execute("ALTER TABLE articles ADD COLUMN description TEXT")
    if 'tag' not in cols:
        db.execute("ALTER TABLE articles ADD COLUMN tag TEXT")
    if 'cover_image' not in cols:
        db.execute("ALTER TABLE articles ADD COLUMN cover_image TEXT")
    if 'last_editor_id' not in cols:
        db.execute("ALTER TABLE articles ADD COLUMN last_editor_id INTEGER REFERENCES users(id)")
    db.commit()

    # Migration: add friend_code to users table if missing
    cols = [row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'friend_code' not in cols:
        db.execute("ALTER TABLE users ADD COLUMN friend_code TEXT")
        # Генерируем коды для существующих пользователей
        import random
        import string
        users = db.execute("SELECT id FROM users").fetchall()
        for user in users:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            db.execute("UPDATE users SET friend_code=? WHERE id=?", (code, user['id']))
        # После заполнения добавляем UNIQUE constraint
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_friend_code ON users(friend_code) WHERE friend_code IS NOT NULL")
    db.commit()

    # Создаем таблицу оценок если её нет
    db.execute("""
        CREATE TABLE IF NOT EXISTS article_ratings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            user_id    INTEGER REFERENCES users(id),
            rating     INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(article_id, user_id)
        )
    """)
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
