from flask import Blueprint, render_template, request, session
from app.db import get_db

main = Blueprint('main', __name__)


@main.route('/')
def index():
    db = get_db()
    recent = db.execute(
        "SELECT a.*, u.username FROM articles a JOIN users u ON a.author_id=u.id ORDER BY a.created_at DESC LIMIT 6"
    ).fetchall()
    return render_template('index.html', recent=recent)


@main.route('/search')
def search():
    q = request.args.get('q', '').strip()
    articles = []
    users = []
    if q:
        db = get_db()
        articles = db.execute(
            "SELECT * FROM articles WHERE title LIKE ? OR body LIKE ? ORDER BY rating DESC",
            (f'%{q}%', f'%{q}%')
        ).fetchall()
        users = db.execute(
            "SELECT id, username, role, bio FROM users WHERE username LIKE ?",
            (f'%{q}%',)
        ).fetchall()
    return render_template('search.html', q=q, results=articles, users=users)
